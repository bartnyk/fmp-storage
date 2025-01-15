import logging
import os
import time
from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from core.components.errors import ScrapperNotPreparedException, TickerNotAvailableException
from core.components.scrapper import BaseScrapper
from core.components.utils import wait_random
from core.config import cfg

logger = logging.getLogger("scrapper_logger")


class ForexCSVDataScrapper(BaseScrapper):
    source_url: str = str(cfg.fmp.forex_csv_source_url)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._options.add_experimental_option(
            "prefs",
            {
                "download.default_directory": cfg.project_path.forex_csv_directory,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
            },
        )
        self._file_name = None

    @wait_random(0.03, 0.5)
    def _change_format(self):
        el = self._driver.find_element(By.ID, "select-format")
        Select(el).select_by_value("0")

    @property
    def available_symbols(self) -> list[str]:
        symbol_element = self._driver.find_element(By.ID, "select-symbol")
        symbol = Select(symbol_element)
        return [option.get_property("value") for option in symbol.options]

    @wait_random(0.03, 0.5)
    def _change_settings(self):
        self._driver.find_element(By.XPATH, '//*[@data-panel-switch="settings"]').click()
        time.sleep(0.05)
        tz_el = self._driver.find_element(By.ID, "select-timezone")
        bars_el = self._driver.find_element(By.ID, "select-max-bars")

        Select(tz_el).select_by_value("80000050")
        Select(bars_el).select_by_value("200000")

    def _run_loading(self):
        self._driver.find_element(By.ID, "btn-load-data").click()

    def _select_ticker(self, ticker: str):
        self._select_symbol(ticker)
        self._run_loading()
        self._driver.find_element(By.XPATH, '//*[@data-panel-switch="acquisition"]').click()

    def _download(self):
        tr_element = self._driver.find_element(By.ID, "table-acquisition").find_elements(By.TAG_NAME, "tr")[3]
        download_element = WebDriverWait(tr_element, 10).until(EC.presence_of_element_located((By.TAG_NAME, "a")))
        self._file_name = tr_element.text
        download_element.click()
        sleep(1)
        self._wait_for_download()

    @wait_random(0.03, 0.5)
    def _select_symbol(self, ticker: str):
        if ticker not in self.available_symbols:
            raise TickerNotAvailableException(f"Ticker {ticker} is not available.")

        symbol_element = self._driver.find_element(By.ID, "select-symbol")
        Select(symbol_element).select_by_value(ticker)

    def setup(self):
        self._change_format()
        self._change_settings()
        self._ready = True

    def get_data(self, ticker: str, *args, **kwargs):
        if not self._ready:
            raise ScrapperNotPreparedException("Scrapper is not prepared yet.")

        logger.info(f"Downloading CSV file for {ticker}.")
        self._select_ticker(ticker)
        self._download()

    def _wait_for_download(self, timeout=10):
        start_time = time.time()
        file_path = os.path.join(cfg.project_path.forex_csv_directory, self._file_name)

        while time.time() - start_time < timeout:
            if any(fname.endswith(".crdownload") for fname in os.listdir(cfg.project_path.forex_csv_directory)):
                time.sleep(1)
            else:
                logger.info(f"Successfully downloaded the file: " f"{file_path}.")
                break
        else:
            raise TimeoutError(f"Pobieranie trwało zbyt długo: {file_path}")
