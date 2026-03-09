# shared/delpi_auth/request_context.py

from contextvars import ContextVar

_current_user = ContextVar("current_user", default=None)


def set_current_user(user):
    _current_user.set(user)


def get_current_user():
    return _current_user.get()