"""
Module for custom exceptions.

"""

from abc import ABCMeta


class BaseMessageException(Exception, metaclass=ABCMeta):
    """Base exception class for displaying messages."""

    __message = None

    def __init__(self, message: str = None) -> None:
        self.message = message or self.__message


class NoDataException(BaseMessageException): ...


class NoProxyLoadedException(BaseMessageException): ...


class ScrapperUrlNotDefinedException(BaseMessageException): ...
