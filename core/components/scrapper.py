import logging
import random
from abc import abstractmethod

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from seleniumwire import webdriver
from webdriver_manager.chrome import ChromeDriverManager

from core.components.errors import ScrapperUrlNotDefinedException
from core.config import cfg
from core.consts import USER_AGENTS

logger = logging.getLogger("scrapper_logger")


class BaseScrapper:
    source_url: str = None

    def __init__(self, gui: bool = False, use_proxy: bool = True) -> None:
        self._gui = gui
        self._use_proxy = use_proxy
        self._driver = None
        self._ready = False

        if self.source_url is None:
            raise ScrapperUrlNotDefinedException(f"{self.__class__} has no source_url attribute defined.")

        self._options = Options()
        self._options.add_argument("--disable-blink-features=AutomationControlled")
        self._options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self._options.add_experimental_option("useAutomationExtension", False)
        self._options.add_argument("--window-size=2560,1440")

        user_agent = random.choice(USER_AGENTS)
        self._options.add_argument(f"user-agent={user_agent}")

        if not gui:
            self._options.add_argument("--headless=now")
            self._options.add_argument("--disable-gpu")

    def shutdown(self) -> None:
        self._driver.quit()

    def _setup_driver(self):
        params = {
            "options": self._options,
            "service": Service(ChromeDriverManager().install()),
            "seleniumwire_options": {},
        }

        if self._use_proxy:
            params["seleniumwire_options"]["proxy"] = cfg.proxy.seleniumwire_proxy

        self._driver = webdriver.Chrome(**params)
        self._driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """
            },
        )
        self._driver.get(self.source_url)

    def __enter__(self):
        self._setup_driver()
        self._driver.implicitly_wait(5)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

        if exc_type:
            logger.error(f"Exception occurred: {exc_val}\n{exc_tb}")

    @abstractmethod
    def get_data(self, *args, **kwargs):
        pass

    @abstractmethod
    def setup(self, *args, **kwargs):
        pass
