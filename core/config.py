"""
Configuration module.

This module contains configuration classes and settings for the application.
It includes configurations for MongoDB, stock API, paths, proxies etc.
"""

import logging.config
import os
import random
from datetime import UTC
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

from core.errors import NoProxyLoadedException
from core.models import Interval, Period


class MongoDBConfig(BaseSettings):
    """
    MongoDB configuration class.

    Attributes
    ----------
    host : str
        The hostname of the MongoDB server.
    port : int
        The port number on which the MongoDB server is listening.
    db_name : str
        The name of the MongoDB database.
    user : Optional[str]
        The username for MongoDB authentication.
    password : Optional[str]
        The password for MongoDB authentication.
    """

    host: str = "localhost"
    port: int = 27017
    db_name: str = "stock"
    user: Optional[str]
    password: Optional[str]

    @property
    def url(self) -> str:
        """
        Returns the MongoDB connection URL.

        Returns
        -------
        str
            The MongoDB connection URL.
        """
        auth = f"{self.user}:{self.password}@" if len(self.user) > 0 else ""
        return f"mongodb://{auth}{self.host}:{self.port}/{self.db_name}"


class StockConstsConfig:
    """
    Stock API constants configuration class.

    Attributes
    ----------
    default_stock_data_interval : Interval
        The default interval for stock data.
    default_stock_data_period : Period
        The default period for stock data.
    default_forex_pairs : list[str]
        The list of default forex pairs.
    """

    default_stock_data_interval: Interval = Interval.FIVE_MINUTES
    default_stock_data_period: Period = Period.ONE_MONTH
    default_forex_pairs: list[str] = []

    def read_default_forex_pairs(self, file_path: str) -> None:
        """
        Reads default forex pairs from the file.

        Parameters
        ----------
        file_path : str
            Path to the file (.txt) with default forex pairs.
        """
        with open(file_path, mode="r") as file:
            self.default_forex_pairs = file.read().splitlines()


class StockConfig(BaseSettings):
    """
    Stock API configuration class.

    Attributes
    ----------
    events_url : str
        The URL for stock events scrapper.
    consts : StockConstsConfig
        The constants configuration for stock API.
    """

    events_url: str
    consts: StockConstsConfig = StockConstsConfig()


class PathConfig:
    """
    Paths configuration class.

    Attributes
    ----------
    root_directory : str
        The root directory of the project.
    assets_directory : str
        The directory for assets.
    logging_config : str
        The path to the logging configuration file.
    proxy_list : str
        The path to the proxy list file.
    forex_pairs : str
        The path to the forex pairs file.
    """

    root_directory: str = os.getcwd()
    assets_directory: str = os.path.join(root_directory, "assets")
    logging_config: str = os.path.join(assets_directory, "logging.ini")
    proxy_list: str = os.path.join(assets_directory, "proxy.txt")
    forex_pairs: str = os.path.join(assets_directory, "forex_pairs.txt")


class ProxyConfig(BaseSettings):
    """
    Proxy configuration class.

    Attributes
    ----------
    ip_list : list[str]
        The list of static proxy IPs.
    current : str
        The current proxy IP.
    username : Optional[str]
        The username for proxy authentication.
    password : Optional[str]
        The password for proxy authentication.
    host : Optional[str]
        The proxy host.
    port : Optional[str]
        The proxy port.
    ssl : bool
        Whether to use SSL for the proxy connection.
    """

    # static - provided directly from file.
    ip_list: list[str] = ()
    current: str = ""

    # dynamic - provided from proxy rotation service.
    username: Optional[str]
    password: Optional[str]
    host: Optional[str]
    port: Optional[str]
    ssl: bool = False

    @property
    def url(self) -> Optional[str]:
        """
        Returns the proxy URL.

        Returns
        -------
        Optional[str]
            URL to the proxy rotation service.
        """
        if self.host is None:
            return None

        protocol = "https" if self.ssl else "http"
        auth = f"{self.username}:{self.password}@" if self.username else ""
        port = f":{self.port}" if self.port else ""

        return f"{protocol}://{auth}{self.host}{port}"

    def shuffle(self) -> Optional[str]:
        """
        Shuffles the proxy list.

        Returns
        -------
        Optional[str]
            Current proxy.

        Raises
        ------
        NoProxyLoadedException
            If the proxy list is empty.
        """
        if not self.available:
            return

        if not self.ip_list:
            raise NoProxyLoadedException("Proxy list is empty.")

        list_copy = list(self.ip_list)

        if self.current in self.ip_list:
            list_copy.remove(self.current)

        self.current = random.choice(list_copy)
        return self.current

    def read_proxies(self, file_path: str) -> None:
        """
        Reads proxies from the file.

        Parameters
        ----------
        file_path : str
            Path to the file (.txt) with proxies.
        """
        with open(file_path, mode="r") as file:
            self.ip_list = file.read().splitlines()

    @property
    def available(self) -> bool:
        """
        Checks if the proxy list is available.

        Returns
        -------
        bool
            True if the proxy list is available, False otherwise.
        """
        return bool(self.ip_list)

    @property
    def seleniumwire_proxy(self) -> dict:
        """
        Returns the proxy configuration for SeleniumWire.

        Returns
        -------
        dict
            Proxy configuration for SeleniumWire.
        """
        return {"http": self.url, "https": self.url}


class Config(BaseSettings):
    """
    Application configuration class.

    Attributes
    ----------
    mongodb : MongoDBConfig
        The MongoDB configuration.
    project_path : PathConfig
        The paths configuration.
    stock : StockConfig
        The stock API configuration.
    proxy : ProxyConfig
        The proxy configuration.
    model_config : SettingsConfigDict
        The settings configuration dictionary.
    """

    mongodb: MongoDBConfig
    project_path: PathConfig = PathConfig()
    stock: StockConfig
    proxy: ProxyConfig

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        case_sensitive=False,
        env_file=".env",
        extra="allow",
    )

    @property
    def timezone(self):
        """
        Returns the timezone.

        Returns
        -------
        timezone
            Timezone.
        """
        return UTC

    def model_post_init(self, *args, **kwargs):
        """
        Runs after the model initialization.
        """
        self.stock.consts.read_default_forex_pairs(self.project_path.forex_pairs)
        self.proxy.read_proxies(self.project_path.proxy_list)


cfg = Config()
logging.config.fileConfig(cfg.project_path.logging_config)
