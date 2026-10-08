from contextlib import contextmanager

@contextmanager
def temporary_value(mapping, key, value):
    existed = key in mapping
    if existed:
        initial_value = mapping[key]
    mapping[key] = value

    try:
        yield
    finally:
        if existed:
            mapping[key] = initial_value
        else:
            mapping.pop(key, None)