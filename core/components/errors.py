import logging

from fmp.errors import BaseMessageException

scraper_logger = logging.getLogger("scraper_logger")


class ScrapperException(BaseMessageException):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(logger=scraper_logger, *args, **kwargs)


class YahooTickerObjectNotDefinedException(BaseMessageException):
    """Exception raised when a Yahoo ticker object is not defined."""

    __message = "Yahoo ticker object not defined."


class ClientUpdateTypeNotDefinedException(BaseMessageException):
    """Exception raised when a client update type is not defined."""

    __message = "Client update type not defined."


class ScrapperUrlNotDefinedException(ScrapperException): ...


class ScrapperNotPreparedException(ScrapperException): ...


class TickerNotAvailableException(ScrapperException): ...
