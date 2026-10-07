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
    async def parse_number():
        raise UnicodeError

    res = None
    with pytest.raises(UnicodeError):
        res = await parse_number()

    assert res == 0




