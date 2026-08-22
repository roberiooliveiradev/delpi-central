from __future__ import annotations

from fastapi import Request


def _display_name_from_user(user: object) -> str | None:
    if isinstance(user, dict):
        for key in ("name", "full_name", "username"):
            value = user.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    for attr in ("name", "full_name", "username"):
        value = getattr(user, attr, None)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def actor_from_request(request: Request) -> tuple[str | None, str | None, str | None]:
    """Extract user_id, email and display name from the JWT (delpi_auth SimpleNamespace)."""
    user = getattr(request.state, "user", None)
    if user is None:
        return None, None, None

    if isinstance(user, dict):
        user_id = user.get("sub") or user.get("user_id") or user.get("id")
        email = user.get("email")
    else:
        user_id = (
            getattr(user, "id", None)
            or getattr(user, "sub", None)
            or getattr(user, "user_id", None)
        )
        email = getattr(user, "email", None)

    user_name = _display_name_from_user(user)
    if user_name and email and user_name.lower() == str(email).lower():
        user_name = None

    return (str(user_id) if user_id else None, str(email) if email else None, user_name)


def actor_from_user(user: object) -> tuple[str | None, str | None, str | None]:
    if user is None:
        return None, None, None
    if isinstance(user, dict):
        user_id = user.get("sub") or user.get("user_id") or user.get("id")
        email = user.get("email")
    else:
        user_id = (
            getattr(user, "id", None)
            or getattr(user, "sub", None)
            or getattr(user, "user_id", None)
        )
        email = getattr(user, "email", None)
    user_name = _display_name_from_user(user)
    if user_name and email and user_name.lower() == str(email).lower():
        user_name = None
    return (str(user_id) if user_id else None, str(email) if email else None, user_name)
