from asyncio import CancelledError
import inspect

import pytest

from async_decorator_fallback import fallback_async


async def test_success():
    @fallback_async(default=0)
    async def parse_number(text: str) -> int:
        return int(text)

    assert await parse_number('4') == 4


async def test_value_error():
    @fallback_async(default=0)
    async def parse_number(text: str) -> int:
        return int(text)

    assert await parse_number('value error') == 0


async def test_sub_value_error():
    @fallback_async(default=0)
    async def raise_unicode_error():
        raise UnicodeError

    assert await raise_unicode_error() == 0


async def test_runtime_error():
    @fallback_async(default=0)
    async def parse_number():
        raise RuntimeError

    with pytest.raises(RuntimeError) as exc_info:
        await parse_number()

    assert RuntimeError == type(exc_info.value)


async def test_cancelled_error():
    @fallback_async(default=0)
    async def parse_number():
        raise CancelledError

    with pytest.raises(CancelledError):
        await parse_number()


async def test_default_identity():
    indentity = []
    @fallback_async(default=indentity)
    async def parse_number(text: str) -> int:
        return int(text)

    res = await parse_number('value error')
    assert res is indentity


async def test_initial_result_on_success():
    @fallback_async(default=1)
    async def false_return():
        return False

    @fallback_async(default=1)
    async def zero_return():
        return 0

    @fallback_async(default=1)
    async def none_return():
        return None
    
    assert await false_return() is False
    assert await zero_return() == 0
    assert await none_return() is None


async def test_no_additional_tries():
    call_count = 0

    @fallback_async(default=0)
    async def parse_number(text: str) -> int:
        nonlocal call_count
        call_count += 1
        return int(text)

    await parse_number('5')
    assert call_count == 1

    await parse_number('5')
    await parse_number('5')
    assert call_count == 3


async def test_args_and_metadata_identity():
    default = 0
    async def get_value(a, b, c=1):
        '''sums three numbers'''
        return a + b + c

    wrapped = fallback_async(default=default)(get_value)

    assert await wrapped(1, 2) == 4
    assert await wrapped(1, 2, c=3) == 6

    assert wrapped.__doc__ == 'sums three numbers'
    assert wrapped.__name__ == 'get_value'
    assert inspect.signature(wrapped) == inspect.signature(get_value)

