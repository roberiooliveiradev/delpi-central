# shared/delpi_auth/request_context.py

from contextvars import ContextVar

_current_user = ContextVar("current_user", default=None)


def set_current_user(user):
    return _current_user.set(user)


def reset_current_user(token):
    _current_user.reset(token)


def clear_current_user():
    _current_user.set(None)


def get_current_user():
    return _current_user.get()