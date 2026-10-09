from typing import Callable
from functools import wraps

def trace_async(events: list[str]):
    def wrapper(coro: Callable):
        @wraps(coro)
        async def inner(*args, **kwargs):
            events.append('start')
            try:
                return await coro(*args, **kwargs)
            except Exception as e:
                raise e
            finally:
                events.append('finish')
            
        return inner
    return wrapper
