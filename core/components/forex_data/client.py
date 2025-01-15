import logging
from abc import abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import yfinance as yf
from fmp.repository.models import ForexPair, ForexTickerList
from fmp.repository.utils import handle_insert_error
from pandas import DataFrame
from pymongo.errors import BulkWriteError

from core.components.client import FMPClient
from core.components.errors import ClientUpdateTypeNotDefinedException, YahooTickerObjectNotDefinedException
from core.components.forex_data.crawler import ForexDataCSVCrawler
from core.components.forex_data.scrapper import ForexCSVDataScrapper
from core.config import cfg
from core.consts import ForexUpdateType, Interval, Period

__all__ = ["DefaultForexDataClient"]

logger = logging.getLogger("forex_data_logger")

COLUMNS_HISTORICAL = ["Ticker", "Date", "Open", "High", "Low", "Close"]
COLUMNS_LATEST = ["Ticker", "Datetime", "Open", "High", "Low", "Close"]


class ForexDataClient(FMPClient):
    @property
    def tickers(self) -> list[ForexPair]:
        """
        Cached property of all available Forex tickers.

        Returns
        -------
        list[ForexPair]
            List of ForexPair objects.

        """
        return ForexPair.parse_list(cfg.fmp.consts.default_forex_pairs)

    async def _save(self, forex_tickers_list: ForexTickerList) -> None:
        """
        Update the database with a list of ForexTicker objects.

        Parameters
        ----------
        forex_tickers_list : ForexTickerList
            List of ForexTicker objects.

        """
        await self._repository.ensure_indexes()

        if len(forex_tickers_list) > 10000:
            for chunk in [forex_tickers_list[i : i + 10000] for i in range(0, len(forex_tickers_list), 10000)]:
                await self._save_chunk(ForexTickerList.model_validate(chunk))
        else:
            await self._save_chunk(forex_tickers_list)

    async def _save_chunk(self, documents: ForexTickerList) -> None:
        try:
            await self._repository.insert_many(documents.model_dump(), ordered=False)
        except BulkWriteError as e:
            handle_insert_error(e)

    def _parse(self, data: DataFrame, *args, **kwargs) -> ForexTickerList:
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
        return ForexTickerList.model_validate(data.to_dict(orient="records"))

    @abstractmethod
    def _download(self, *args, **kwargs):
        pass

    @abstractmethod
    def _update(self, *args, **kwargs):
        pass

    @abstractmethod
    def update_historical(self, *args, **kwargs) -> None:
        pass

    @abstractmethod
    def update_latest(self, *args, **kwargs) -> None:
        pass


class YahooFinanceDataClient(ForexDataClient):
    def __init__(self, *args, **kwargs):
        self._yf: Optional[yf.Ticker | yf.Tickers] = None
        self._update_state: Optional[ForexUpdateType] = None
        super().__init__(*args, **kwargs)

    def for_single_ticker(self, ticker: ForexPair) -> None:
        self._yf = yf.Ticker(ticker.yf)

    def for_multiple_tickers(self, tickers: list[ForexPair]) -> None:
        self._yf = yf.Tickers([ticker.yf for ticker in tickers])

    async def update_historical(self):
        self._update_state = ForexUpdateType.HISTORICAL
        await self._update(start=datetime(2018, 1, 1).strftime("%Y-%m-%d"))

    async def update_latest(self):
        self._update_state = ForexUpdateType.LATEST
        await self._update(interval=Interval.FIVE_MINUTES.value, period=Period.MAX.value)

    @property
    def columns(self):
        if not self._update_state:
            raise ClientUpdateTypeNotDefinedException

        if self._update_state == ForexUpdateType.HISTORICAL:
            return COLUMNS_HISTORICAL
        elif self._update_state == ForexUpdateType.LATEST:
            return COLUMNS_LATEST

    @property
    def index_column(self):
        if not self._update_state:
            raise ClientUpdateTypeNotDefinedException

        if self._update_state == ForexUpdateType.HISTORICAL:
            return "Date"
        elif self._update_state == ForexUpdateType.LATEST:
            return "Datetime"

    async def _update(self, *args, **kwargs) -> None:
        if not self._yf:
            raise YahooTickerObjectNotDefinedException

        yahoo_df: DataFrame = self._download(**kwargs)

        if yahoo_df.empty:
            logger.error("Failed to download data. Aborting.")
            return
        else:
            logger.info(f"Downloaded {len(yahoo_df)} rows of data.")

        forex_data: ForexTickerList = self._parse(yahoo_df)
        logger.info(f"Parsed {len(forex_data)} tickers out of downloaded data.")

        await self._save(forex_data)
        logger.info("Saved new data to the database.")

    def _download(self, *args, **kwargs):
        return self._yf.history(*args, **kwargs)

    def _parse(self, data: DataFrame, *args, **kwargs) -> ForexTickerList:  # noqa
        """
        Parse the downloaded data into a list of ForexTicker objects.

        Parameters
        ----------
        data : DataFrame
            Downloaded data from Yahoo Finance.
        columns : list[str]
            List of columns to parse.

        Returns
        -------
        ForexTickerList
            List of ForexTicker objects.

        """
        data.index.name = self.index_column
        data = data.stack(level=1, future_stack=True).reset_index()
        data = data.dropna(subset=["Close", "Open", "High", "Low"])
        data = data[self.columns]
        data["Ticker"] = data["Ticker"].str.replace("=X", "").apply(ForexPair.from_raw)

        return super()._parse(data)


class ForexDataCSVClient(ForexDataClient):
    def _download(self, *args, **kwargs):
        pass

    def _update(self, *args, **kwargs):
        pass

    def update_historical(self, *args, **kwargs) -> None:
        pass

    def update_latest(self, *args, **kwargs) -> None:
        pass

    async def update_all(self, *args, **kwargs) -> None:
        for file_name in Path(cfg.project_path.forex_csv_directory).iterdir():
            ticker_df = None
            if file_name.is_file() and file_name.suffix == ".csv":
                ticker = file_name.name.split("_")[0]
                data = pd.read_csv(file_name, names=["Datetime", "Open", "High", "Low", "Close", "Volume"])
                data["Datetime"] = pd.to_datetime(data["Datetime"], utc=True)
                data["Ticker"] = ForexPair.from_raw(ticker)
                logger.info(f"Loaded {len(data)} rows from {file_name}.")

                forex_data = self._parse(data)
                logger.info(f"Parsed {len(forex_data)} rows for {ticker}.")

                await self._save(forex_data)
                logger.info("Saved new data to the database.")

    @property
    def tickers(self) -> list[str]:
        return [
            "EURUSD",
            "GBPUSD",
            "USDCAD",
            "USDCHF",
            "USDJPY",
            "AUDCAD",
            "AUDCHF",
            "AUDJPY",
            "AUDUSD",
            "CADCHF",
            "CADJPY",
            "CHFJPY",
            "EURAUD",
            "EURCAD",
            "EURCHF",
            "EURGBP",
            "EURJPY",
            "GBPAUD",
            "GBPCAD",
            "GBPCHF",
            "GBPJPY",
        ]

    def download_files(
        self,
    ) -> None:
        crawler = ForexDataCSVCrawler(tickers=self.tickers, scrapper_class=ForexCSVDataScrapper)
        crawler.crawl()


DefaultForexDataClient = YahooFinanceDataClient  # define default client
