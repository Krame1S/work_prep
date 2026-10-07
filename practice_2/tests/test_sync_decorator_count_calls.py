import pytest
import inspect
from sync_decorator_count_calls import count_calls


def test_initial_count_is_zero():
    @count_calls
    def func():
        pass
    # не вызываем
    assert func.call_count == 0


def test_several_successing_calls():
    @count_calls
    def func():
        pass
    # вызываем 3 раза
    func()
    func()
    func()

    assert func.call_count == 3


def test_one_call_with_error():
    @count_calls
    def func():
        raise ValueError

    with pytest.raises(ValueError):
        func()
    # один колл с ошибкой должен инкрементировать call_count
    assert func.call_count == 1
 

def test_two_funcs_independence():
    @count_calls
    def func1():
        pass

    @count_calls
    def func2():
        pass
    # вызываем первую один раз
    func1()

    # вызываем вторую два раза
    func2()
    func2()

    assert func1.call_count == 1
    assert func2.call_count == 2


def test_result_identity():
    ret = ['unique result']

    @count_calls
    def func():
        return ret

    res = func()

    assert res is ret
    

def test_exception_identity():
    error = ValueError()

    @count_calls
    def func():
        raise error

    with pytest.raises(ValueError) as exc_info:
        func()

    assert exc_info.value is error
    

def test_arguments_are_passed_through():
    @count_calls
    def func(a, b):
        return (a, b)

    assert func(1, 2) == (1, 2)
    assert func(a=1, b=2) == (1, 2)
    assert func(1, b=2) == (1, 2)


def test_metadata_is_preserved():
    def original(a, b=1):
        '''doc'''

    wrapped = count_calls(original)

    assert wrapped.__name__ == original.__name__
    assert wrapped.__doc__ == original.__doc__
    assert inspect.signature(wrapped) == inspect.signature(original)