from contextlib import asynccontextmanager
from typing import Callable


@asynccontextmanager
async def managed_connection(connect: Callable):
    connection = await connect()
    try:
        yield connection
    finally:
        await connection.aclose()
