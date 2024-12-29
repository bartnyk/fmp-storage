from typing import Type

from core.repository import MongoDBRepository


class StockClient:
    def __init__(self, repository: Type[MongoDBRepository]) -> None:
        self._repository: MongoDBRepository = repository()
