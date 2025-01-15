"""
Command line interface for the FMP Storage.

"""

import asyncio
import logging
import time
from datetime import date, datetime
from functools import wraps
from typing import Callable, Optional

from fmp.repository.models import ForexPair
from fmp.repository.mongo import ForexDataRepository, ForexEconomicEventsRepository
from typer import Option, Typer

from core import DefaultEconomicEventsClient, DefaultForexDataClient
from core.components.economic_events.crawler import EconomicEventsCrawler
from core.components.forex_data.client import ForexDataCSVClient

cli = Typer(pretty_exceptions_enable=False)
logger: logging.Logger = logging.getLogger("cli_logger")


def async_command(func: Callable) -> Callable:
    """
    Decorator to run a command asynchronously.

    Parameters
    ----------
    func : Callable
        The function to be decorated.

    Returns
    -------
    Callable
        The decorated function.
    """

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
async def get_historical_forex_data() -> None:
    """
    Update the historical forex data for predefined tickers.

    This function initializes the forex data client, sets the tickers, and updates the historical data.
    """
    forex_data_client = DefaultForexDataClient(ForexDataRepository)
    tickers = forex_data_client.tickers
    forex_data_client.for_multiple_tickers(tickers)
    await forex_data_client.update_historical()


@cli.command(name="update-latest-forex-data")
@async_command
async def get_latest_forex_data() -> None:
    """
    Update the latest forex data for already available tickers.

    This function initializes the forex data client, sets the tickers, and updates the latest data.
    """
    forex_data_client = DefaultForexDataClient(ForexDataRepository)
    tickers: list[ForexPair] = forex_data_client.tickers
    forex_data_client.for_multiple_tickers(tickers)
    await forex_data_client.update_latest()


@cli.command(name="update-historical-economic-events")
@async_command
async def get_historical_forex_events(
    gui: bool = Option(False, "--gui", "-g"),
    start_date_str: Optional[str] = Option(None, "--start"),
    end_date_str: Optional[str] = Option(None, "--end"),
) -> None:
    """
    Update historical forex news and events.

    Parameters
    ----------
    gui : bool, optional
        Whether to use the GUI by scrapper, by default False.
    start_date_str : Optional[str], optional
        The start date in the format 'dd-mm-yyyy', by default None.
    end_date_str : Optional[str], optional
        The end date in the format 'dd-mm-yyyy', by default None.
    """
    start_date: Optional[date] = datetime.strptime(start_date_str, "%d-%m-%Y").date() if start_date_str else None
    end_date: Optional[date] = datetime.strptime(end_date_str, "%d-%m-%Y").date() if end_date_str else None

    economic_events_client = DefaultEconomicEventsClient(
        crawler=EconomicEventsCrawler, repository=ForexEconomicEventsRepository
    )
    date_ranges = economic_events_client.create_date_ranges(start_date, end_date)
    await economic_events_client.update_for_dates(date_ranges, shuffle_dates=True, gui=gui)


@cli.command(name="update-latest-economic-events")
@async_command
async def get_latest_forex_events(gui: bool = Option(False, "--gui", "-g")) -> None:
    """
    Update the latest forex events.

    Parameters
    ----------
    gui : bool, optional
        Whether to use the GUI by scrapper, by default False.
    """
    economic_events_client = DefaultEconomicEventsClient(
        crawler=EconomicEventsCrawler, repository=ForexEconomicEventsRepository
    )
    await economic_events_client.update_recent_events(gui=gui)


@cli.command(name="download-forex-csv")
@async_command
async def download_csv_forex_data() -> None:
    """
    Download the forex data as a CSV file.
    """
    forex_data_client = ForexDataCSVClient(ForexDataRepository)
    forex_data_client.download_files()


@cli.command(name="update-forex-data-from-csv")
@async_command
async def update_forex_data_from_csv() -> None:
    """
    Download the forex data as a CSV file.
    """
    forex_data_client = ForexDataCSVClient(ForexDataRepository)
    await forex_data_client.update_all()


if __name__ == "__main__":
    cli()
