from functools import wraps


def as_list(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        return list(func(*args, **kwargs))
    return wrapped
