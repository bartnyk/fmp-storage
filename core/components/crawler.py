from abc import abstractmethod
from typing import Type

from core.components.scrapper import BaseScrapper


class BaseCrawler:
    def __init__(self, scrapper_class: Type[BaseScrapper], gui: bool = False, max_retries: int = 5):
        self._scrapper_class: Type[BaseScrapper] = scrapper_class
        self._gui = gui
        self._max_retries_on_error = max_retries
        self._attempt = 0

    @abstractmethod
    def crawl(self, *args, **kwargs) -> None:
        pass
