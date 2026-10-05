from typing import Callable
from functools import wraps
import time


def retry(*, attempts: int, delay: float = 0.0):
    if attempts < 1:
        raise ValueError("attempts must be >= 1")
    if delay < 0:
        raise ValueError("delay must be >= 0")

    def wrapper(unstable_op: Callable):
        @wraps(unstable_op)
        def inner(*args, **kwargs):
            for attempt in range(attempts):
                try:
                    return unstable_op(*args, **kwargs)
                except Exception: 
                    if attempt == attempts - 1:
                        raise 
                    time.sleep(delay)
        return inner
    return wrapper


