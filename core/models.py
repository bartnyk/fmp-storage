from enum import Enum

from pydantic import RootModel


class ListBaseModel(RootModel):
    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def __len__(self):
        return len(self.root)


class Period(Enum):
    ONE_DAY = "1d"  # 1 day
    FIVE_DAYS = "5d"  # 5 days
    ONE_MONTH = "1mo"  # 1 month
    THREE_MONTHS = "3mo"  # 3 months
    SIX_MONTHS = "6mo"  # 6 months
    ONE_YEAR = "1y"  # 1 year
    TWO_YEARS = "2y"  # 2 years
    FIVE_YEARS = "5y"  # 5 years
    TEN_YEARS = "10y"  # 10 years
    YEAR_TO_DATE = "ytd"  # Year to date
    MAX = "max"  # Maximum available period


class Interval(Enum):
    ONE_MINUTE = "1m"  # 1 minute
    TWO_MINUTES = "2m"  # 2 minutes
    FIVE_MINUTES = "5m"  # 5 minutes
    FIFTEEN_MINUTES = "15m"  # 15 minutes
    THIRTY_MINUTES = "30m"  # 30 minutes
    SIXTY_MINUTES = "60m"  # 60 minutes
    NINETY_MINUTES = "90m"  # 90 minutes
    ONE_DAY = "1d"  # 1 day
    FIVE_DAYS = "5d"  # 5 days
    ONE_WEEK = "1wk"  # 1 week
    ONE_MONTH = "1mo"  # 1 month
