from datetime import datetime
from enum import Enum

from core.models import ListBaseModel
from pydantic import AwareDatetime, BaseModel, model_validator
from pydantic.dataclasses import dataclass


@dataclass
class CountrySubject:
    name: str
    currency: str


class Country(Enum):
    """Country subject enumeration class."""

    USA = "United States"
    EU = "Euro Area"
    Japan = "Japan"
    UK = "United Kingdom"
    Australia = "Australia"
    Canada = "Canada"
    Switzerland = "Switzerland"
    China = "China"
    Mexico = "Mexico"
    India = "India"
    Russia = "Russia"
    Turkey = "Turkey"
    Poland = "Poland"

    @property
    def _currencies(self) -> dict:
        return {
            self.USA: "USD",
            self.EU: "EUR",
            self.Japan: "JPY",
            self.UK: "GBP",
            self.Australia: "AUD",
            self.Canada: "CAD",
            self.Switzerland: "CHF",
            self.China: "CNY",
            self.Mexico: "MXN",
            self.India: "INR",
            self.Russia: "RUB",
            self.Turkey: "TRY",
            self.Poland: "PLN",
        }

    @property
    def currency(self) -> str:
        """
        Get the currency of the country.

        Returns
        -------
        str
            Currency code.

        """
        return self._currencies[self]

    @property
    def subject(self) -> CountrySubject:
        """
        Get the CountrySubject object.

        Returns
        -------
        CountrySubject
            Country subject object.

        """
        return CountrySubject(name=self.value, currency=self.currency)

    @classmethod
    def get_subject_names(cls) -> list[str]:
        """Get the list of country subject names."""
        return [subject.value for subject in cls]


class Event(BaseModel, validate_assignment=True, use_enum_values=True):
    timestamp: AwareDatetime
    title: str
    subject: CountrySubject
    actual: str
    previous: str
    consensus: str
    forecast: str
    created_at: datetime = datetime.now()  # no need for utc
    updated_at: datetime = datetime.now()  # no need for utc

    @model_validator(mode="before")
    def updated_at_signal(self) -> "Event":
        """Change updated_at value on each model change."""
        self["updated_at"] = datetime.now()
        return self


class EventList(ListBaseModel):
    root: list[Event]
