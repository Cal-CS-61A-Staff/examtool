from functools import wraps
from os import getenv

import requests

from api.auth import get_token, refresh_token


def server_only(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        kwargs.update(dict(zip(func.__code__.co_varnames, args)))
        if getenv("ENV") == "SERVER":
            return func(**kwargs)
        else:
            method = func.__name__
            try:
                return call_server(method, kwargs)
            except PermissionError:
                refresh_token()
            return call_server(method, kwargs)

    return wrapped


def call_server(method, kwargs):
    token = get_token()
    resp = requests.post(
        "https://exam.cs61a.org/admin/api/{method}".format(method=method),
        json={**kwargs, "token": token},
    )
    if resp.status_code == 200:
        return resp.json()
    elif resp.status_code == 401:
        raise PermissionError
    else:
        raise Exception
