from typing import Type

from core.repository.mongo import MongoDBRepository


class StockClient:
    def __init__(self, repository: Type[MongoDBRepository]) -> None:
        self._repository: MongoDBRepository = repository()
