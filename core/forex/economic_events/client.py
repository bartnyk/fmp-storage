import logging
import random
import time
from datetime import datetime, timedelta
from typing import Type

from core.config import cfg
from core.forex.client import StockClient
from core.forex.economic_events.crawler import StockDataCrawler
from core.forex.economic_events.models import EventList
from core.forex.economic_events.scrapper import DEFAULT_SCRAPPER_CLASS

logger = logging.getLogger("economic_events_logger")

__all__ = ["DefaultEconomicEventsClient"]


class EconomicEventsClient(StockClient):
    def __init__(self, crawler: Type[StockDataCrawler], scrapper=DEFAULT_SCRAPPER_CLASS, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._crawler_class = crawler
        self._scrapper_class = scrapper

    async def upsert_events(self, events: EventList) -> tuple[int, int, int]:
        await self._repository.ensure_indexes()
        inserted = updated = error = 0
        for event in events:
            try:
                res = await self._repository.update_one(
                    {"title": event.title, "timestamp": event.timestamp, "subject.name": event.subject.name},
                    event.model_dump(),
                    upsert=True,
                )
            except Exception as e:
                logger.error(f"Error while upserting event: {e}")
                error += 1
            else:
                if res.upserted_id is not None:
                    inserted += 1
                elif res.modified_count > 0:
                    updated += 1
        return inserted, updated, error

    async def update_for_dates(
        self, date_ranges: list[tuple[datetime.date, datetime.date]], shuffle_dates: bool = True, gui: bool = False
    ):
        if shuffle_dates:
            random.shuffle(date_ranges)

        crawler = self._crawler_class(self._scrapper_class, date_ranges, gui=gui)

        while not crawler.iteration_done:
            events_list: list[EventList] = crawler.crawl()
            inserted = updated = error = 0

            for events in events_list:
                i, u, e = await self.upsert_events(events)
                inserted += i
                updated += u
                error += e

            logger.info(f"New events: {inserted}, Updated events: {updated}, Errors: {error}")
            wait_for = random.randint(3, 12)
            logger.info(f"Done: {crawler.percentage_done * 100:.2f}%")

            if crawler.iteration_done:
                break

            logger.info(f"Waiting for {wait_for} seconds before summoning fresh scrapper.")
            time.sleep(wait_for)

    async def update_recent_events(self, gui: bool = False):
        with self._scrapper_class(gui=gui, recent_only=True) as scrapper:
            scrapper.setup()
            events = scrapper.get_data()
            events_list: EventList = scrapper.parse_objects(events)
            inserted, updated, error = await self.upsert_events(events_list)
            logger.info(f"New events: {inserted}, Updated events: {updated}, Errors: {error}")

    async def get_present_dates(self) -> list[datetime.date]:
        return await self._repository.get_present_dates()

    @staticmethod
    def create_date_ranges(start_date: datetime.date = None) -> list[tuple[datetime.date, datetime.date]]:
        """
        Create date ranges from past.

        Parameters
        ----------
        start_date : datetime.date
            Start date. Default is 5 years ago.

        Returns
        -------
        list[tuple[datetime.date, datetime.date]]
            List of date ranges.

        """
        today = datetime.now(tz=cfg.timezone).date()

        if start_date is None:
            start_date = today - timedelta(weeks=5 * 52)  # 5 years ago

        date_pairs = []

        while start_date < today:
            end_date = start_date + timedelta(days=6)
            date_pairs.append((start_date, end_date))
            start_date += timedelta(weeks=1)

        return date_pairs


DefaultEconomicEventsClient = EconomicEventsClient
