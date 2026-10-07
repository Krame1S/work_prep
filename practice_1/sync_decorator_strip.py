from typing import Callable
from functools import wraps

def strip_result(func: Callable):
    @wraps(func)
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        return res.strip()
    return wrapper
