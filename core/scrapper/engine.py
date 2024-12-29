import logging
import random

from core.config import cfg
from core.errors import ScrapperUrlNotDefinedException
from core.scrapper.utils import USER_AGENTS
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from seleniumwire import webdriver
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger("scrapper_logger")


class BaseScrapper:
    __url__ = None

    def __init__(self, gui: bool = False, use_proxy: bool = True) -> None:
        self._gui = gui

        if self.__url__ is None:
            raise ScrapperUrlNotDefinedException(f"{self.__class__} has no __url__ attribute defined.")

        options = Options()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("--window-size=2560,1440")

        user_agent = random.choice(USER_AGENTS)
        options.add_argument(f"user-agent={user_agent}")

        if not gui:
            options.add_argument("--headless=now")
            options.add_argument("--disable-gpu")

        driver_params = {"options": options, "service": Service(ChromeDriverManager().install())}

        if use_proxy:
            driver_params["seleniumwire_options"] = cfg.proxy.seleniumwire_proxy

        self._driver = webdriver.Chrome(**driver_params)
        self._driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    """
            },
        )
        self._driver.get(self.__url__)

    def shutdown(self) -> None:
        self._driver.quit()

    def __enter__(self):
        self._driver.implicitly_wait(5)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

        if exc_type:
            logger.error(f"Exception occurred: {exc_val}\n{exc_tb}")
