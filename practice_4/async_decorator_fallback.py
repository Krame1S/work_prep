from typing import Callable

def fallback_async(default):
    def wrapper(coro: Callable):
        async def inner(*args, **kwargs):
            try:
                return await coro(*args, **kwargs)
            except ValueError:
                return default
        return inner
    return wrapper
