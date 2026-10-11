import asyncio
from functools import wraps
import pytest
from async_context_manager_open_close import managed_connection


def count_calls(coro):
    @wraps(coro)
    async def wrapper(*args, **kwargs):
        wrapper.call_count += 1
        return await coro(*args, **kwargs) 
    wrapper.call_count = 0
    return wrapper


async def test_open_work_close_order():
    class FakeConnection:
        async def aclose(self):
            order.append('закрытие')
            pass

    async def fake_connect():
        connection = FakeConnection()
        order.append('открытие')
        return connection

    order = []
    async with managed_connection(fake_connect) as connection:
        order.append('работа')

    assert order == ['открытие', 'работа', 'закрытие']


async def test_resource_identity():
    class FakeConnection:
        async def aclose(self):
            pass

    created = FakeConnection()

    async def connect():
        return created

    async with managed_connection(connect) as connection:
        assert connection is created
 

async def test_amount_of_calls():
    class FakeConnection:
        @count_calls
        async def aclose(self):
            pass

    @count_calls
    async def connect_fake():
        connection = FakeConnection()
        return connection


    cm = managed_connection(connect_fake)
    assert connect_fake.call_count == 0
    async with cm as connection:
        pass
        assert connect_fake.call_count == 1
    assert connection.aclose.call_count == 1


async def test_error_on_entering():
    ran = False

    class FakeConnection:
        @count_calls
        async def aclose(self):
            pass

    @count_calls
    async def connect_fake():
        FakeConnection()
        raise RuntimeError

    with pytest.raises(RuntimeError):
        async with managed_connection(connect_fake):
            ran = True

    assert not ran
    assert connect_fake.call_count == 1
    assert FakeConnection.aclose.call_count == 0


async def test_block_error():
    class FakeConnection:
        @count_calls
        async def aclose(self):
            pass

    @count_calls
    async def connect_fake():
        connection = FakeConnection()
        return connection

    exc = RuntimeError

    with pytest.raises(exc) as exc_info:
        async with managed_connection(connect_fake) as connection:
            raise RuntimeError

    assert connection.aclose.call_count == 1


async def test_block_cancel():
    event1 = asyncio.Event()
    event2 = asyncio.Event()

    class FakeConnection:
        @count_calls
        async def aclose(self):
            pass

    connection = FakeConnection()

    async def connect_fake():
        return connection

    async def coro():
        async with managed_connection(connect_fake):
            event1.set()
            await event2.wait()
            
    task = asyncio.create_task(coro())
    await event1.wait()
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task

    assert connection.aclose.call_count == 1
