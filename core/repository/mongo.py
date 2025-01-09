"""
Module for MongoDB repositories.

"""

import logging
from abc import ABC
from typing import Optional

from core.components.forex_data.models import ForexPair, ForexTicker
from core.config import cfg
from core.repository.errors import CollectionNameNotDefinedException
from core.repository.models import MongoDBIndex
from core.repository.utils import log_repo_action
from motor.motor_asyncio import (AsyncIOMotorClient, AsyncIOMotorCollection,
                                 AsyncIOMotorCursor, AsyncIOMotorDatabase)
from pydantic import BaseModel, RootModel
from pymongo import DESCENDING, results
from pymongo.errors import ConnectionFailure

logger: logging.Logger = logging.getLogger("db_logger")


class MongoDBRepository(ABC):
    """
    MongoDB repository abstract class. Each MongoDB collection has its own repository class.

    Attributes
    ----------
    __collection_name : Optional[str]
        Name of the collection associated with the repository.
    __model : Optional[BaseModel]
        Pydantic model associated with the repository.
    indexes : tuple[MongoDBIndex | tuple[MongoDBIndex], bool]
        Indexes to create in the collection.
        Tuple of MongoDBIndex objects or tuples of MongoDBIndex objects and a boolean value (is unique?).

    """

    __collection_name: Optional[str] = None
    __model: Optional[BaseModel] = None

    indexes: tuple[MongoDBIndex | tuple[MongoDBIndex], bool] = ()

    def __init__(self) -> None:
        """
        Initialize the MongoDB repository with a client and database connection.

        Raises
        ------
        CollectionNameNotDefinedException
            If the collection name is not defined.
        """
        self._client: AsyncIOMotorClient = AsyncIOMotorClient(cfg.mongodb.url)

        try:
            self._client.admin.command("ping")
            logger.info(f"Successfully connected to MongoDB: ({cfg.mongodb.url})")
        except ConnectionFailure:
            logger.error("Failed to connect to MongoDB")

        self._db: AsyncIOMotorDatabase = self._client[cfg.mongodb.db_name]
        self._indexes_updated: bool = False

        if collection_name := getattr(self, f"_{self.__class__.__name__}__collection_name"):
            self._collection: AsyncIOMotorCollection = self._db[collection_name]
        else:
            raise CollectionNameNotDefinedException(self.__class__)

    async def ensure_indexes(self) -> None:
        """
        Ensure that the indexes are created in the collection.

        """
        for index, is_unique in self.indexes:
            parsed_index = (
                index.as_tuple if isinstance(index, MongoDBIndex) else [element.as_tuple for element in index]
            )
            await self._collection.create_index(parsed_index, unique=is_unique)

        self._indexes_updated = True

    @log_repo_action(logger)
    async def insert_one(self, document: BaseModel, *args, **kwargs) -> results.InsertOneResult:
        """
        Insert a single document into the collection.

        Parameters
        ----------
        document : BaseModel
            Pydantic model object.

        Returns
        -------
        InsertOneResult
            Insert result object.
        """
        return await self._collection.insert_one(document, *args, **kwargs)

    @log_repo_action(logger)
    async def insert_many(self, documents: RootModel, *args, **kwargs) -> results.InsertManyResult:
        """
        Insert multiple documents into the collection.

        Parameters
        ----------
        documents : list of BaseModel
            List of Pydantic model objects.

        Returns
        -------
        InsertManyResult
            Insert result object.
        """
        return await self._collection.insert_many(documents.model_dump(), *args, **kwargs)

    @log_repo_action(logger)
    async def find(self, query: dict, *args, **kwargs) -> AsyncIOMotorCursor:
        """
        Retrieve documents from the collection.

        Parameters
        ----------
        query : dict
            Query dictionary.

        Returns
        -------
        AsyncIOMotorCursor
            Cursor object.
        """
        return self._collection.find(query, *args, **kwargs)

    @log_repo_action(logger)
    async def find_one(self, query: dict, *args, **kwargs) -> dict:
        """
        Retrieve a single document from the collection.

        Parameters
        ----------
        query : dict
            Query dictionary.

        Returns
        -------
        dict
            Document object.

        """
        res = await self._collection.find_one(query, *args, **kwargs)
        res["mongo_object_id"] = res.pop("_id", None)
        return res

    @log_repo_action(logger)
    async def update_one(self, query: dict, update: dict, **kwargs) -> results.UpdateResult:
        """
        Update a single document in the collection.

        Parameters
        ----------
        query : dict
            Query dictionary.
        update : dict
            Update dictionary.

        Returns
        -------
        UpdateResult
            Update result object.
        """
        return await self._collection.update_one(query, {"$set": update}, **kwargs)

    @log_repo_action(logger)
    async def update_many(self, query: dict, update: dict, *args, **kwargs) -> results.UpdateResult:
        """
        Update multiple documents in the collection.

        Parameters
        ----------
        query : dict
            Query dictionary.
        update : dict
            Update dictionary.

        Returns
        -------
        UpdateResult
            Update result object.
        """
        return await self._collection.update_many(query, update, *args, **kwargs)

    @log_repo_action(logger)
    async def delete_one(self, query: dict, *args, **kwargs) -> results.DeleteResult:
        """
        Delete a single document from the collection.

        Parameters
        ----------
        query : dict
            Query dictionary.

        Returns
        -------
        DeleteResult
            Delete result object.
        """
        return await self._collection.delete_one(query, *args, **kwargs)

    @log_repo_action(logger)
    async def delete_many(self, query: dict, *args, **kwargs) -> results.DeleteResult:
        """
        Delete multiple documents from the collection.

        Parameters
        ----------
        query : dict
            Query dictionary.

        Returns
        -------
        DeleteResult
            Delete result object.
        """
        return await self._collection.delete_many(query, *args, **kwargs)


class ForexDataRepository(MongoDBRepository):
    """
    MongoDB repository class for fmp data.

    Attributes
    ----------
    __collection_name : Optional[str]
        Name of the collection associated with the repository.
    __model : Optional[BaseModel]
        Pydantic model associated with the repository.
    indexes : tuple[MongoDBIndex | tuple[MongoDBIndex], bool]
        Indexes to create in the collection.
        Tuple of MongoDBIndex objects or tuples of MongoDBIndex objects and a boolean value (is unique?).

    """

    __collection_name = "forex_data"
    __model: BaseModel = ForexTicker

    indexes: tuple[MongoDBIndex | tuple[MongoDBIndex], bool] = (
        (
            (
                MongoDBIndex(key="ticker", direction=DESCENDING),
                MongoDBIndex(key="timestamp", direction=DESCENDING),
            ),
            True,
        ),
    )

    async def get_latest_for_ticker(self, ticker: ForexPair) -> dict:
        """
        Get the latest document for a ticker.

        Parameters
        ----------
        ticker : str
            Ticker symbol.

        Returns
        -------
        dict
            Document object.
        """

        return await self.find_one({"ticker": ticker.raw}, sort=[("timestamp", DESCENDING)])

    async def get_available_tickers(self) -> list[str]:
        """
        Get the available tickers in the collection.

        Returns
        -------
        list[str]
            List of ticker symbols.
        """
        return await self._collection.distinct("ticker")


class ForexEconomicEventsRepository(MongoDBRepository):
    __collection_name = "economic_events"
    __model: BaseModel = ForexTicker

    indexes: tuple[MongoDBIndex | tuple[MongoDBIndex], bool] = (
        (
            (
                MongoDBIndex(key="timestamp", direction=DESCENDING),
                MongoDBIndex(key="title", direction=DESCENDING),
                MongoDBIndex(key="subject.name", direction=DESCENDING),
            ),
            True,
        ),
    )

    async def get_present_dates(self) -> list[str]:
        return await self._collection.distinct("timestamp.$date")
