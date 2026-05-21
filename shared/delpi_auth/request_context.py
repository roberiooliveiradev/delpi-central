# shared/delpi_auth/request_context.py

from contextvars import ContextVar

_current_user = ContextVar("current_user", default=None)
_request_authorization = ContextVar("request_authorization", default=None)


def set_current_user(user):
    return _current_user.set(user)


def reset_current_user(token):
    _current_user.reset(token)


def clear_current_user():
    _current_user.set(None)


def get_current_user():
    return _current_user.get()


def set_request_authorization(authorization: str | None):
    return _request_authorization.set(authorization)


def get_request_authorization() -> str | None:
    return _request_authorization.get()


def reset_request_authorization(token) -> None:
    _request_authorization.reset(token)


def clear_request_authorization() -> None:
    _request_authorization.set(None)