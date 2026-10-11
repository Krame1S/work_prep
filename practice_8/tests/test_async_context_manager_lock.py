import asyncio

import pytest

from async_context_manager_lock import HoldLock

async def test_lock_identity_and_states():
    lock = asyncio.Lock()
    cm = HoldLock(lock)
    assert not lock.locked()
    async with cm as current:
        assert current is lock
        assert lock.locked()
    assert not lock.locked()


async def test_free_lock_on_error():
    lock = asyncio.Lock()
    exc = RuntimeError()
    with pytest.raises(RuntimeError) as exc_info:
        async with HoldLock(lock):
            raise exc

    assert exc_info.value is exc
    assert not lock.locked()


async def test_free_lock_on_cancel():
    event1 = asyncio.Event()
    event2 = asyncio.Event()

    lock = asyncio.Lock()
    async def coro():
        async with HoldLock(lock):
            event1.set()
            await event2.wait()

    task = asyncio.create_task(coro())
    await event1.wait()
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task

    assert task.cancelled()
    assert not lock.locked()


async def test_cancel_waiting_does_not_release_others_lock():
    event1 = asyncio.Event()
    event2 = asyncio.Event()

    lock = asyncio.Lock()

    async def coro():
        async with HoldLock(lock):
            event2.set()
            await event1.wait()

    task1 = asyncio.create_task(coro())
    task2 = asyncio.create_task(coro())

    await event2.wait()
    task2.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task2

    assert task2.cancelled()
    assert lock.locked()

    event1.set()
    await task1
    assert not lock.locked()



