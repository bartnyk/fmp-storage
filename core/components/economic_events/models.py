from datetime import datetime

from pydantic import AwareDatetime, BaseModel, Field, model_validator
from pydantic.dataclasses import dataclass

from fmp.repository.models import ListBaseModel


@dataclass
class CountrySubject:
    name: str
    currency: str


class Event(BaseModel, validate_assignment=True, use_enum_values=True):
    timestamp: AwareDatetime
    title: str
    subject: CountrySubject
    actual: str
    previous: str
    consensus: str
    forecast: str
    sentiment: int = Field(ge=0, le=1)  # -1: negative, 1: positive, 0: possible error
    created_at: datetime = datetime.now()  # no need for utc
    updated_at: datetime = datetime.now()  # no need for utc

    @model_validator(mode="before")
    def updated_at_signal(self) -> "Event":
        """Change updated_at value on each model change."""
        self["updated_at"] = datetime.now()
        return self


class EventList(ListBaseModel):
    root: list[Event]
