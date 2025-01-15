import logging
import random

from core.components.crawler import BaseCrawler
from core.components.errors import TickerNotAvailableException

logger = logging.getLogger("forex_data_logger")


class ForexDataCSVCrawler(BaseCrawler):
    def __init__(self, tickers: list[str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tickers = tickers
        self._original_tickers_count = len(tickers)

    def crawl(self, *args, **kwargs) -> None:
        while self._tickers:
            tickers_number = random.randint(3, 6)
            # tickers_to_crawl = self._tickers
            if len(self._tickers) <= 6:
                tickers_to_crawl = self._tickers
                self._remove_tickers(self._tickers)
            else:
                tickers_to_crawl = self._cut_tickers_list(tickers_number)

            # with self._scrapper_class(gui=self._gui) as scrapper:
            with self._scrapper_class() as scrapper:
                scrapper.setup()

                for ticker in tickers_to_crawl:
                    try:
                        scrapper.get_data(ticker)
                    except TickerNotAvailableException:
                        continue

    def _cut_tickers_list(self, tickers_number: int) -> list[str]:
        tickers = random.sample(self._tickers, tickers_number)
        self._remove_tickers(tickers)
        return tickers

    def _remove_tickers(self, tickers: list[str]) -> None:
        if tickers == self._tickers:
            self._tickers = []

        self._tickers = [date for date in self._tickers if date not in tickers]

    @property
    def iteration_done(self) -> bool:
        return len(self._tickers) == 0

    @property
    def percentage_done(self) -> float:
        return (self._original_tickers_count - len(self._tickers)) / self._original_tickers_count
