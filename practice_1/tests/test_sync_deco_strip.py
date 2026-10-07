import pytest
from sync_decorator_strip import strip_result
import inspect


@strip_result
def greeting(name: str, *, punctuation: str = "!") -> str:
    return f"  Привет, {name}{punctuation}  "


def test_regular_string():
    assert greeting("Илья", punctuation="?") == "Привет, Илья?"


def test_empty_string():
    assert greeting('') == 'Привет, !'


def test_only_space_str():
    assert greeting('     ') == 'Привет,      !'


def test_inner_spaces_preserved():
    assert greeting('Сан Санович Саныч ') == 'Привет, Сан Санович Саныч !'


def test_args_and_kwargs():
    assert greeting('Имя') == "Привет, Имя!"
    assert greeting(name='Имя', punctuation="...") == "Привет, Имя..."


def test_called_once():
    calls = 0

    @strip_result
    def counter():
        nonlocal calls
        calls += 1
        return "  ok  "

    assert counter() == "ok"
    assert calls == 1


def test_same_exception_rises():
    @strip_result
    def exc():
        raise ValueError

    with pytest.raises(ValueError) as exc_info:
        exc()
    
    assert ValueError == type(exc_info.value)


def test_metadata_preserved():
    def original(a: int, *, b: str = "x") -> str:
        """Doc"""
        return f"  {a}{b}  "

    decorated = strip_result(original)

    assert decorated.__name__ == "original"
    assert decorated.__doc__ == "Doc"
    assert inspect.signature(decorated) == inspect.signature(original)