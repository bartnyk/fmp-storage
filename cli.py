"""
Command line interface for the FMP Storage.

"""

import asyncio
import logging
import time
from datetime import datetime
from functools import wraps

from typer import Option, Typer

from core import DefaultEconomicEventsClient, DefaultForexDataClient
from core.components.economic_events.crawler import EconomicEventsCrawler
from core.components.forex_data.models import ForexPair
from core.config import cfg
from core.errors import NoDataException
from core.repository.mongo import (ForexDataRepository,
                                   ForexEconomicEventsRepository)

cli = Typer(pretty_exceptions_enable=False)
logger: logging.Logger = logging.getLogger("cli_logger")


def async_command(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_id, func_name = id(func), func.__name__
        func_desc = f"{func_name}[id:{func_id}]"
        start_time = time.time()

        logger.info(f"Running command {func_desc}.")

        try:
            asyncio.run(func(*args, **kwargs))
        except Exception as e:
            logger.error(f"Error during command {func_desc}: {e}")
            raise e
        else:
            duration = time.time() - start_time
            logger.info(f"Command {func_desc} completed successfully in {duration:.2f} seconds.")

    return wrapper


@cli.command(name="update-historical-forex-data")
@async_command
async def get_historical_forex_data(ticker: str = Option(None, "--ticker", "-t")) -> None:
    """
    Update the historical forex data for predefined tickers.

    """
    forex_data_client = DefaultForexDataClient(ForexDataRepository)
    if ticker:
        tickers: list[ForexPair] = [ForexPair.from_raw(ticker)]
    else:
        tickers: list[ForexPair] = ForexPair.parse_list(cfg.fmp.consts.default_forex_pairs)

    for ticker in tickers:
        try:
            await forex_data_client.update_historical_data(ticker)
        except NoDataException as e:
            logger.error(e)
        else:
            logger.info(f"Data for {ticker} updated successfully.")


@cli.command(name="update-detailed-forex-data")
@async_command
async def get_detailed_forex_data(ticker: str = Option(None, "--ticker", "-t")) -> None:
    """
    Update the detailed forex data for predefined tickers.

    """
    forex_data_client = DefaultForexDataClient(ForexDataRepository)

    if ticker:
        tickers: list[ForexPair] = [ForexPair.from_raw(ticker)]
    else:
        tickers: list[ForexPair] = ForexPair.parse_list(cfg.fmp.consts.default_forex_pairs)

    for ticker in tickers:
        try:
            await forex_data_client.update_detailed_data(ticker)
        except NoDataException as e:
            logger.error(e)
        else:
            logger.info(f"Data for {ticker} updated successfully.")


@cli.command(name="update-latest-forex-data")
@async_command
async def get_latest_forex_data(ticker: str = Option(None, "--ticker", "-t")) -> None:
    """
    Update the latest forex data for already available tickers.

    """
    forex_data_client = DefaultForexDataClient(ForexDataRepository)

    if ticker:
        tickers: list[ForexPair] = [ForexPair.from_raw(ticker)]
    else:
        tickers: list[ForexPair] = await forex_data_client.available_tickers

    for ticker in tickers:
        try:
            await forex_data_client.update_latest_data(ticker)
        except NoDataException as e:
            logger.error(e)
        else:
            logger.info(f"Data for {ticker} updated successfully.")


@cli.command(name="update-historical-economic-events")
@async_command
async def get_historical_forex_events(
    gui: bool = Option(False, "--gui", "-g"),
    start_date_str: str = Option(None, "--start"),
    end_date_str: str = Option(None, "--end"),
):
    """
    Update historical forex news and events.

    """
    start_date = datetime.strptime(start_date_str, "%d-%m-%Y").date() if start_date_str else None
    end_date = datetime.strptime(end_date_str, "%d-%m-%Y").date() if end_date_str else None

    economic_events_client = DefaultEconomicEventsClient(
        crawler=EconomicEventsCrawler, repository=ForexEconomicEventsRepository
    )
    date_ranges = economic_events_client.create_date_ranges(start_date, end_date)
    await economic_events_client.update_for_dates(date_ranges, shuffle_dates=True, gui=gui)


@cli.command(name="update-latest-economic-events")
@async_command
async def get_latest_forex_events(gui: bool = Option(False, "--gui", "-g")):
    """
    Update forex events.

    """
    economic_events_client = DefaultEconomicEventsClient(
        crawler=EconomicEventsCrawler, repository=ForexEconomicEventsRepository
    )
    await economic_events_client.update_recent_events(gui=gui)


if __name__ == "__main__":
    cli()
