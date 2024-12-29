"""
Module for repository exceptions.

"""

from core.errors import BaseMessageException


class CollectionNameNotDefinedException(BaseMessageException):
    """
    Exception raised when the collection name is not defined in the child class of repository.

    """

    __message = "Collection name in {repo_class} is not defined."

    def __init__(self, repository_class: type) -> None:
        """
        :param repository_class: Repository class.
        """
        self.__message = self.__message.format(repo_class=repository_class)
        super().__init__()


class RepositoryNotImplementedException(BaseMessageException):
    """
    Exception raised when repository is not implemented in the child class of use case.

    """

    __message = "Repository not implemented."
