import functools
import random
import time


def wait_random(min_seconds: float = 0.2, max_seconds: float = 1.0):
    """
    Decorator to wait a random amount of time after executing the decorated function.

    Parameters
    ----------
    min_seconds : float
        Minimum time to wait.
    max_seconds : float
        Maximum time to wait.

    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            wait_time = random.uniform(min_seconds, max_seconds)
            time.sleep(wait_time)
            return func(*args, **kwargs)

        return wrapper

    return decorator
