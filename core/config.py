"""
Configuration module.

This module contains configuration classes and settings for the application.
It includes configurations for MongoDB, APIs, paths, proxies etc.
"""

import logging.config
import os
import random
from typing import Optional

from fmp.config import Config as CoreConfig
from fmp.errors import NoProxyLoadedException
from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class FMPConsts:
    """
    FMP constants configuration class.

    Attributes
    ----------
    default_forex_pairs : list[str]
        The list of default forex pairs.
    """

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


class FMPConfig(BaseSettings):
    """
    FMP setup/configuration class.

    Attributes
    ----------
    events_source_url : HttpUrl
        Source URL for economic events.
    consts : FMPConsts
        The constants configuration.
    """

    events_source_url: HttpUrl
    forex_csv_source_url: HttpUrl
    consts: FMPConsts = FMPConsts()


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
    forex_csv_directory : str
        The directory for forex CSV files.
    """

    root_directory: str = os.getcwd()
    assets_directory: str = os.path.join(root_directory, "assets")
    forex_csv_directory: str = os.path.join(assets_directory, "forex_csv")
    logging_config: str = os.path.join(root_directory, "logging.ini")
    proxy_list: str = os.path.join(assets_directory, "proxy_list.txt")
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

    ip_list: list[str] = ()
    current: str = ""

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
            return None

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
    def seleniumwire_proxy(self) -> dict:  # noqa
        """
        Returns the proxy configuration for SeleniumWire.

        Returns
        -------
        dict
            Proxy configuration for SeleniumWire.
        """
        return {"http": self.url, "https": self.url}


class Config(CoreConfig):
    """
    Application configuration class.

    Attributes
    ----------
    project_path : PathConfig
        Project paths configuration.
    fmp : FMPConfig
        Forex defaults/setup configuration.
    proxy : ProxyConfig
        Proxy configuration - dynamic/static.
    model_config : SettingsConfigDict
        Pydantic model configuration.
    """

    project_path: PathConfig = PathConfig()
    fmp: FMPConfig
    proxy: ProxyConfig

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        case_sensitive=False,
        env_file=".env",
        extra="allow",
    )

    def model_post_init(self, *args, **kwargs):
        """
        Runs after the model initialization.
        """
        self.fmp.consts.read_default_forex_pairs(self.project_path.forex_pairs)
        self.proxy.read_proxies(self.project_path.proxy_list)


cfg = Config()  # noqa
logging.config.fileConfig(cfg.project_path.logging_config)
