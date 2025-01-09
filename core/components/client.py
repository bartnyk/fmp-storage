from typing import Type

from core.repository.mongo import MongoDBRepository


class FMPClient:
    def __init__(self, repository: Type[MongoDBRepository]) -> None:
        self._repository: MongoDBRepository = repository()
