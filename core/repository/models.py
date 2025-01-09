from dataclasses import dataclass
from enum import Enum
from typing import Optional, Union

from bson import ObjectId
from core.components.forex_data.models import Currency
from core.config import cfg
from core.models import ListBaseModel
from pandas import Timestamp
from pydantic import (AwareDatetime, BaseModel, ConfigDict, Field,
                      field_serializer, model_serializer, model_validator)
from pymongo import ASCENDING, DESCENDING


class MongoModel(BaseModel):
    """Base MongoDB model class."""

    # mongo_object_id: Optional[PydanticObjectId] = None
    mongo_object_id: Optional[ObjectId]

    model_config = ConfigDict(use_enum_values=True, arbitrary_types_allowed=True)


class SymbolType(Enum):
    """Symbol type enumeration class."""

    CURRENCY = "Currency"
    CRYPTO = "Crypto"


class SymbolEntity(MongoModel):
    """Base symbol model class."""

    name: str = Field(alias="currency name")
    code: str = Field(alias="currency code")


class Symbol(SymbolEntity):
    """Symbol model class."""

    symbol_type: SymbolType


@dataclass
class MongoDBIndex:
    key: str
    direction: Union[ASCENDING, DESCENDING]

    @property
    def as_tuple(self) -> tuple[str, Union[ASCENDING, DESCENDING]]:
        return self.key, self.direction


@dataclass
class ForexPair:
    base: Currency
    quote: Currency

    @property
    def yf(self) -> str:
        return f"{self.base.value}{self.quote.value}=X"

    @property
    def raw(self) -> str:
        return f"{self.base.value}{self.quote.value}"

    @classmethod
    def from_raw(cls, raw_str: str) -> "ForexPair":
        if len(raw_str) != 6:
            raise ValueError(f"Invalid Forex pair format: {raw_str}")
        return cls(base=Currency(raw_str[:3]), quote=Currency(raw_str[3:]))

    @model_serializer
    def serializer(self) -> str:
        return self.raw

    @property
    def currencies(self) -> tuple[Currency, Currency]:
        return self.base, self.quote

    @classmethod
    def parse_list(cls, list_raw_str: list[str]) -> list["ForexPair"]:
        return [cls.from_raw(raw_str) for raw_str in list_raw_str]


class ForexTicker(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ticker: ForexPair
    timestamp: Optional[AwareDatetime] = Field(alias="Datetime", default=None)
    adj_close: Optional[float] = Field(default=None, alias="Adj Close")
    close: float = Field(alias="Close")
    high: float = Field(alias="High")
    low: float = Field(alias="Low")
    open: float = Field(alias="Open")
    volume: int = Field(alias="Volume")

    @field_serializer("ticker")
    def ticker_serializer(self, ticker: ForexPair) -> str:
        return ticker.raw

    @model_validator(mode="before")
    def date_to_datetime(self) -> "ForexTicker":
        if not self.get("timestamp"):
            self["timestamp"] = self.get("Date", None) or self.get("Datetime", None)
        if isinstance(self["timestamp"], Timestamp):
            self["timestamp"] = self["timestamp"].to_pydatetime()
        self["timestamp"] = self["timestamp"].replace(tzinfo=cfg.timezone)
        return self

    @model_validator(mode="before")
    def str_to_ticker(self) -> "ForexTicker":
        if isinstance(self.get("ticker"), str):
            self["ticker"] = ForexPair.from_raw(self["ticker"])
        return self


class ForexTickerList(ListBaseModel):
    root: list[ForexTicker]
