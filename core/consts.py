from enum import Enum


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


class ForexUpdateType(Enum):
    """Forex update type enumeration class."""

    HISTORICAL = "historical"
    LATEST = "latest"


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; Pixel 3 XL Build/QD1A.190821.007) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.15 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4632.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.2 Safari/537.36",
]
