from __future__ import annotations

from fastapi import Request


def _user_attr(user: object | dict, *keys: str) -> str | None:
    if isinstance(user, dict):
        for key in keys:
            value = user.get(key)
            if value:
                return str(value)
        return None
    for key in keys:
        value = getattr(user, key, None)
        if value:
            return str(value)
    return None


def actor_sub_from_request(request: Request) -> str | None:
    user = getattr(request.state, "user", None)
    if user is None:
        return None
    return _user_attr(user, "sub", "id", "user_id")


def current_user_from_request(request: Request):
    return getattr(request.state, "user", None)
