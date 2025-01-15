import logging
import random
import time
from datetime import datetime

from core.components.crawler import BaseCrawler
from core.components.economic_events.models import EventList

logger = logging.getLogger("economic_events_logger")


class EconomicEventsCrawler(BaseCrawler):
    def __init__(self, date_ranges: list[tuple[datetime.date, datetime.date]] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if date_ranges:
            self._date_ranges: list[tuple[datetime.date, datetime.date]] = date_ranges
            self._original_dates_count = len(date_ranges)

    def crawl(self, *args, **kwargs) -> list[EventList]:
        dates_q = random.randint(2, 5)
        self._attempt = 0

        if len(self._date_ranges) <= 5:
            dates_to_crawl = self._date_ranges
            self._remove_dates(self._date_ranges)
        else:
            dates_to_crawl = self._cut_original_date_ranges(dates_q)

        return self._safe_crawl(dates_to_crawl)

    def _safe_crawl(self, dates_to_crawl: list[tuple[datetime.date, datetime.date]]) -> list[EventList]:
        while self._attempt < self._max_retries_on_error:
            try:
                return self._start_crawling(dates_to_crawl)
            except Exception as e:
                self._attempt += 1
                logger.error(f"Error during crawling attempt {self._attempt}: {e}")
                if self._attempt < self._max_retries_on_error:
                    logger.info(
                        f"Retrying in 20 seconds... (Attempt {self._attempt + 1} of {self._max_retries_on_error})"
                    )
                    time.sleep(20)
                else:
                    logger.error("Max retries reached. Exiting.")
                    raise e

    def _start_crawling(self, dates_to_crawl: list[tuple[datetime.date, datetime.date]]) -> list[EventList]:
        stored_events: [list[EventList]] = []

        with self._scrapper_class(gui=self._gui) as scrapper:
            logger.info(f"Getting economic events for {dates_to_crawl}.")

            for date_range in dates_to_crawl:
                scrapper.setup(from_date=date_range[0], to_date=date_range[1])
                data = scrapper.get_data()
                logger.info(
                    f"Received {len(data)} events between {date_range[0].strftime('%Y-%m-%d')} and {date_range[1].strftime('%Y-%m-%d')}."
                )
                stored_events.append(scrapper.parse_objects(data))
                wait_for = random.randint(1, 3)
                logger.info(f"Waiting for {wait_for} seconds between changing dates.")
                time.sleep(wait_for)

            return stored_events

    def _cut_original_date_ranges(self, dates_to_cut: int) -> list[tuple[datetime.date, datetime.date]]:
        """
        Pick dates_to_cut number of date ranges from the original list.
        Update the original list by removing the picked date ranges.

        Parameters
        ----------
        dates_to_cut : int
            Number of date ranges to pick.

        Returns
        -------
        list[tuple[datetime.date, datetime.date]]
            List of date ranges.

        """
        dates = random.sample(self._date_ranges, dates_to_cut)
        self._remove_dates(dates)
        return dates

    def _remove_dates(self, dates: list[tuple[datetime.date, datetime.date]]) -> None:
        """
        Remove the given dates from the original list.

        Parameters
        ----------
        dates : list[tuple[datetime.date, datetime.date]]
            List of date ranges.

        """
        if dates == self._date_ranges:
            self._date_ranges = []

        self._date_ranges = [date for date in self._date_ranges if date not in dates]

    @property
    def iteration_done(self) -> bool:
        return len(self._date_ranges) == 0

    @property
    def percentage_done(self) -> float:
        return (self._original_dates_count - len(self._date_ranges)) / self._original_dates_count
