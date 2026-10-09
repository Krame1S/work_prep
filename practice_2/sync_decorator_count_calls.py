import functools

def count_calls(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        wrapper.call_count += 1
        res = func(*args, **kwargs)
        return res
    wrapper.call_count = 0    
    return wrapper
