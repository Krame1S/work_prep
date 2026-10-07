import asyncio
import inspect

import pytest

from async_decorator_events import trace_async



async def test_result_and_events_order():
    events: list[str] = []

    @trace_async(events)
    async def get_value():
        return 42

    assert await get_value() == 42
    assert events == ['start', 'finish']


async def test_events_is_empty_before_await():
    events: list[str] = []

    @trace_async(events)
    async def get_value():
        return 42

    assert events == [] # должен быть пустым до await (стоит до await)

    assert await get_value() == 42
    assert events == ['start', 'finish']


async def test_two_sequential_calls():
    events: list[str] = []

    @trace_async(events)
    async def get_value():
        return 42

    assert events == [] # должен быть пустым до await (стоит до await)

    assert await get_value() == 42
    assert await get_value() == 42
    assert events == ['start', 'finish', 'start', 'finish']


async def test_initial_func_error():
    events: list[str] = []

    @trace_async(events)
    async def get_value():
        raise ValueError

    with pytest.raises(ValueError):
        await get_value()

    assert events == ['start', 'finish']


async def test_cancelled_error():
    events: list[str] = []

    @trace_async(events)
    async def get_value():
        raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        await get_value()

    assert events == ['start', 'finish']


async def test_args_and_metadata_identity():
    events: list[str] = []

    async def get_value(a, b, c=1):
        '''sums three numbers'''
        return a + b + c

    wrapped = trace_async(events)(get_value)

    assert await wrapped(1, 2) == 4
    assert await wrapped(1, 2, c=3) == 6
    assert events == ['start', 'finish', 'start', 'finish']

    assert wrapped.__doc__ == 'sums three numbers'
    assert wrapped.__name__ == 'get_value'
    assert inspect.signature(wrapped) == inspect.signature(get_value)