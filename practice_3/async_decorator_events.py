import asyncio
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

events: list[str] = []

@trace_async(events)
async def get_value():
    return 42

async def main():
    print(await get_value())
    print(events)

asyncio.run(main())
