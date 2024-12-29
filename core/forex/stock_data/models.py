from enum import Enum
from typing import Optional

from core.config import cfg
from core.models import ListBaseModel
from pandas import Timestamp
from pydantic import (AwareDatetime, BaseModel, ConfigDict, Field,
                      field_serializer, model_serializer, model_validator)
from pydantic.dataclasses import dataclass


class Currency(Enum):
    USD = "USD"  # United States Dollar
    EUR = "EUR"  # Euro
    JPY = "JPY"  # Japanese Yen
    GBP = "GBP"  # British Pound Sterling
    AUD = "AUD"  # Australian Dollar
    CAD = "CAD"  # Canadian Dollar
    CHF = "CHF"  # Swiss Franc
    CNY = "CNY"  # Chinese Yuan
    HKD = "HKD"  # Hong Kong Dollar
    NZD = "NZD"  # New Zealand Dollar
    SEK = "SEK"  # Swedish Krona
    KRW = "KRW"  # South Korean Won
    SGD = "SGD"  # Singapore Dollar
    NOK = "NOK"  # Norwegian Krone
    MXN = "MXN"  # Mexican Peso
    INR = "INR"  # Indian Rupee
    RUB = "RUB"  # Russian Ruble
    ZAR = "ZAR"  # South African Rand
    TRY = "TRY"  # Turkish Lira
    BRL = "BRL"  # Brazilian Real
    PLN = "PLN"  # Polish Zloty


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
