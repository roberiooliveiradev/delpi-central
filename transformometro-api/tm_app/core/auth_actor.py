from __future__ import annotations

from fastapi import Request


def actor_from_request(request: Request) -> tuple[str | None, str | None]:
    """Extrai user_id e email do JWT (delpi_auth usa SimpleNamespace, não dict)."""
    user = getattr(request.state, "user", None)
    if user is None:
        return None, None

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

    return (str(user_id) if user_id else None, email)
