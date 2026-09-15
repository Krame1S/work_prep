import pytest
from retry_deco import retry

class UnexpectedException(Exception):
    pass 

def test_first_try():
    call_count = 0

    @retry(attempts = 3)
    def simple_func():
        nonlocal call_count
        call_count += 1
        return 'success'

    result = simple_func()

    assert call_count == 1
    assert result == 'success'


def test_two_fall_third_success():
    call_count = 0

    @retry(attempts = 3)
    def fall_on_third_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise UnexpectedException
        else:
            return 'success'

    result = fall_on_third_func()

    assert result == 'success'
    assert call_count == 3


def test_all_attempts_used_check_initial_exc_identity():
    call_count = 0
    total_attempts = 3
    initial_exception = UnexpectedException()

    @retry(attempts = total_attempts)
    def all_attempts_used_func():
        nonlocal call_count
        nonlocal total_attempts
        call_count += 1
        raise initial_exception

    with pytest.raises(UnexpectedException) as exc_info:
        all_attempts_used_func()

    assert exc_info.value is initial_exception
    assert call_count == total_attempts


def test_no_delay_after_last_failure(monkeypatch):
    sleep_calls = []
    total_attempts = 3

    def fake_sleep(seconds):
        sleep_calls.append(seconds)

    monkeypatch.setattr("retry_deco_using_for_loop.time.sleep", fake_sleep)

    @retry(attempts=total_attempts)
    def always_fails_func():
        raise UnexpectedException()

    with pytest.raises(UnexpectedException):
        always_fails_func()

    assert len(sleep_calls) == total_attempts - 1


def test_invalid_attempts():
    with pytest.raises(ValueError) as exc_info_attempts:
        @retry(attempts=0)
        def func1():
            pass

    assert 'attempts' in str(exc_info_attempts.value)


def test_invalid_delay():
    with pytest.raises(ValueError) as exc_info_delay:
        @retry(attempts=1, delay=-1)
        def func2():
            pass

    assert 'delay' in str(exc_info_delay.value)


def test_preserved_metadata():
    @retry(attempts=3)
    def documented_func(x, y):
        '''This function adds two numbers.'''
        return x + y

    assert documented_func.__name__ == 'documented_func'
    assert documented_func.__doc__ == 'This function adds two numbers.'