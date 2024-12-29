from dataclasses import dataclass
from enum import Enum
from typing import Optional, Union

from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict
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
