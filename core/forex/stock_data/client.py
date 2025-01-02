import logging
from abc import abstractmethod
from datetime import UTC, datetime, timedelta
from functools import cached_property
from typing import Optional, Union

import yfinance as yf
from core.config import cfg
from core.errors import NoDataException
from core.forex.client import StockClient
from core.forex.stock_data import models as m
from core.models import Interval, Period
from pandas import DataFrame
from pymongo.errors import BulkWriteError

__all__ = ["DefaultStockDataClient"]

from core.repository.utils import handle_insert_error

logger = logging.getLogger("stock_data_logger")


class StockDataClient(StockClient):
    @cached_property
    async def available_tickers(self) -> list[m.ForexPair]:
        """
        Cached property of all available Forex tickers.

        Returns
        -------
        list[ForexPair]
            List of ForexPair objects.

        """
        return m.ForexPair.parse_list(await self._repository.get_available_tickers())
        # return [m.ForexPair.from_raw(raw_str) for raw_str in await self._repository.get_available_tickers()]

    async def _update_bulk(self, tickers_list: m.ForexTickerList) -> None:  # TODO: insert if historical,
        # update if latest
        """
        Update the database with a list of ForexTicker objects.

        Parameters
        ----------
        tickers_list : ForexTickerList
            List of ForexTicker objects.

        """
        await self._repository.ensure_indexes()

        try:
            await self._repository.insert_many(tickers_list, ordered=False)
        except BulkWriteError as e:  # skip duplicates
            handle_insert_error(e)

    def _parse(self, data: DataFrame, *args, **kwargs) -> m.ForexTickerList:
        """
        Parse the downloaded data into a list of ForexTicker objects.

        Parameters
        ----------
        data : DataFrame
            Dataframe with ticker information.

        Returns
        -------
        ForexTickerList
            List of ForexTicker objects.

        """
        return m.ForexTickerList.model_validate(data.to_dict(orient="records"))

    @abstractmethod
    def update_historical_data(self, ticker: m.ForexPair) -> None:
        pass

    @abstractmethod
    def update_detailed_data(self, ticker: m.ForexPair) -> None:
        pass

    @abstractmethod
    def update_latest_data(self, ticker: Union[m.ForexPair, str]) -> None:
        pass


class YahooFinanceStockDataClient(StockDataClient):
    def _download(
        self,
        tickers: list[m.ForexPair] | m.ForexPair,
        period: Period = cfg.stock.consts.default_stock_data_period,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: Interval = cfg.stock.consts.default_stock_data_interval,
    ) -> DataFrame:
        """
        Download historical data from Yahoo Finance.

        Parameters
        ----------
        tickers : list[ForexPair] | ForexPair
            ForexPair object.
        period : Period
            Period object.
        start_date : Optional[datetime]
            Start date.
        end_date : Optional[datetime]
            End date.
        interval : Interval
            Interval object.

        Returns
        -------
        DataFrame
            Downloaded data from Yahoo Finance as a pandas DataFrame.

        """
        params = {
            "tickers": [ticker.yf for ticker in tickers] if isinstance(tickers, list) else tickers.yf,
            "interval": interval.value,
            "period": period.value,
            "start": start_date,
            "end": end_date,
            "multi_level_index": False,
        }

        if start_date:
            params.pop("period")

        data = yf.download(**params)

        if data.empty:
            raise NoDataException(f"Yahoo Finance returned empty data for: {tickers}")

        return data

    def _parse(self, ticker: m.ForexPair, data: DataFrame) -> m.ForexTickerList:
        """
        Parse the downloaded data into a list of ForexTicker objects.

        Parameters
        ----------
        ticker : ForexPair
            Forex pair object.
        data : DataFrame
            Downloaded data from Yahoo Finance.

        Returns
        -------
        ForexTickerList
            List of ForexTicker objects.

        """
        data = data.reset_index()
        data["ticker"] = ticker
        return super()._parse(data)

    async def update_historical_data(self, ticker: m.ForexPair) -> None:
        """
        Update historical data for a ticker.
        Download historical data from Yahoo Finance with interval of 1 day for the last 5 years.

        Parameters
        ----------
        ticker : Union[ForexPair, str]
            ForexPair object or string representation of the ForexPair.

        """
        options = {"period": Period.FIVE_YEARS, "interval": Interval.ONE_DAY}
        data = self._download(ticker, **options)
        tickers = self._parse(ticker, data)
        await self._update_bulk(tickers)

    async def update_detailed_data(self, ticker: m.ForexPair) -> None:
        """
        Update detailed data for a ticker.
        Download detailed data from Yahoo Finance with interval of 5 minute for the last 60 days.

        Parameters
        ----------
        ticker : ForexPair
            ForexPair object

        """
        options = {"interval": Interval.FIVE_MINUTES}
        data = self._download(ticker, **options)
        tickers = self._parse(ticker, data)
        await self._update_bulk(tickers)

    async def update_latest_data(self, ticker: Union[m.ForexPair, str]) -> None:
        """
        Get and update the latest data for a ticker.
        Based on the latest record in the database, download the latest data from Yahoo Finance
        with interval of 5 minutes. Save the data to the database.

        Parameters
        ----------
        ticker : Union[ForexPair, str]
            Forex pair object or string representation of the Forex pair.

        """
        ticker = m.ForexPair.from_raw(ticker) if isinstance(ticker, str) else ticker

        options = {"interval": Interval.FIVE_MINUTES}
        if latest_record := await self._repository.get_latest_for_ticker(ticker):
            latest_record = m.ForexTicker.model_validate(latest_record)

            if latest_record.timestamp < datetime.now(UTC) - timedelta(days=60):
                return await self.update_historical_data(
                    ticker
                )  # if the latest record is older than 30 days, update historical data for the ticker
            elif datetime.now(UTC) - latest_record.timestamp < timedelta(minutes=5):
                logger.info(f"No need to update the data for {ticker} - last update: " f"{latest_record.timestamp}")
                return

        options["start_date"] = latest_record.timestamp
        data = self._download(ticker, **options)
        tickers = self._parse(ticker, data)
        await self._update_bulk(tickers)
        logger.info(f"Inserted {len(tickers)} records for {ticker}.")


DefaultStockDataClient = YahooFinanceStockDataClient  # define default client
