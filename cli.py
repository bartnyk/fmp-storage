"""
Command line interface for the application.

"""

import asyncio
import logging
from functools import wraps

from typer import Option, Typer

from core import DefaultEconomicEventsClient, DefaultStockDataClient
from core.config import cfg
from core.errors import NoDataException
from core.forex.economic_events.crawler import StockDataCrawler
from core.forex.stock_data.models import ForexPair
from core.repository import (ForexEconomicEventsRepository,
                             ForexStockDataRepository)

cli = Typer(pretty_exceptions_enable=False)
logger: logging.Logger = logging.getLogger("cli_logger")


def async_command(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Running command {func.__name__}")
        return asyncio.run(func(*args, **kwargs))

    return wrapper


@cli.command(name="update-historical-forex-data")
@async_command
async def get_historical_forex_data(ticker: str = Option(None, "--ticker", "-t")) -> None:
    """
    Update the historical stock data for predefined tickers.

    """
    stock_data_client = DefaultStockDataClient(ForexStockDataRepository)
    if ticker:
        tickers: list[ForexPair] = [ForexPair.from_raw(ticker)]
    else:
        tickers: list[ForexPair] = ForexPair.parse_list(cfg.stock.consts.default_forex_pairs)

    for ticker in tickers:
        try:
            await stock_data_client.update_historical_data(ticker)
        except NoDataException as e:
            logger.error(e)
        else:
            logger.info(f"Data for {ticker} updated successfully.")


@cli.command(name="update-detailed-forex-data")
@async_command
async def get_detailed_forex_data(ticker: str = Option(None, "--ticker", "-t")) -> None:
    """
    Update the detailed stock data for predefined tickers.

    """
    stock_data_client = DefaultStockDataClient(ForexStockDataRepository)

    if ticker:
        tickers: list[ForexPair] = [ForexPair.from_raw(ticker)]
    else:
        tickers: list[ForexPair] = ForexPair.parse_list(cfg.stock.consts.default_forex_pairs)

    for ticker in tickers:
        try:
            await stock_data_client.update_detailed_data(ticker)
        except NoDataException as e:
            logger.error(e)
        else:
            logger.info(f"Data for {ticker} updated successfully.")


@cli.command(name="update-latest-forex-data")
@async_command
async def get_latest_forex_data(ticker: str = Option(None, "--ticker", "-t")) -> None:
    """
    Update the latest stock data for already available tickers.

    """
    stock_data_client = DefaultStockDataClient(ForexStockDataRepository)
    if ticker:
        tickers: list[ForexPair] = [ForexPair.from_raw(ticker)]
    else:
        tickers: list[ForexPair] = await stock_data_client.available_tickers

    for ticker in tickers:
        try:
            await stock_data_client.update_latest_data(ticker)
        except NoDataException as e:
            logger.error(e)
        else:
            logger.info(f"Data for {ticker} updated successfully.")


@cli.command(name="update-historical-forex-news")
@async_command
async def get_historical_forex_events(gui: bool = Option(False, "--gui", "-g")) -> None:
    """
    Update historical forex news and events.

    """
    economic_events_client = DefaultEconomicEventsClient(
        crawler=StockDataCrawler, repository=ForexEconomicEventsRepository
    )
    date_ranges = economic_events_client.create_date_ranges()
    await economic_events_client.update_for_dates(date_ranges, shuffle_dates=True, gui=gui)


@cli.command(name="update-forex-events")
@async_command
async def get_forex_events():
    """
    Update forex events.

    """
    economic_events_client = DefaultEconomicEventsClient(ForexStockDataRepository)
    stock_data_client = DefaultStockDataClient(ForexStockDataRepository)

    tickers: list[ForexPair] = await stock_data_client.available_tickers

    # for ticker in tickers:
    #     try:
    #         await yahoo.update_events(ticker)
    #     except NoDataException as e:
    #         logger.error(e)
    #     else:
    #         logger.info(f"Data for {ticker} updated successfully.")


if __name__ == "__main__":
    cli()
