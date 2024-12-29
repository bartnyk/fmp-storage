from functools import wraps
from typing import Any

from pymongo.errors import BulkWriteError


def log_repo_action(logger):
    def decorator(func) -> Any:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            logger.info(
                f"Running [{args[0].__class__.__name__}] {func.__name__} with: {str(args)[:200]}; {str(kwargs)[:200]}."
            )
            result = await func(*args, **kwargs)
            logger.info(
                f"Command [{args[0].__class__.__name__}] {func.__name__} completed. Result: {str(result)[:200]}."
            )
            return result

        return wrapper

    return decorator


def handle_insert_error(err: BulkWriteError) -> None:
    """
    Analyze the BulkWriteError, ignore duplicate key error and raise other errors if any.

    Parameters
    ----------
    err : BulkWriteError
        BulkWriteError object.

    """
    panic_list = list(
        filter(lambda x: x["code"] != 11000, err.details["writeErrors"])
    )  # error other than duplicate key
    if len(panic_list) > 0:
        raise err
