from __future__ import annotations

from fastapi import Request


def actor_sub_from_request(request: Request) -> str | None:
    """Extrai o subject (sub) do JWT autenticado."""
    user = getattr(request.state, "user", None)
    if user is None:
        return None

    if isinstance(user, dict):
        sub = user.get("sub") or user.get("user_id") or user.get("id")
    else:
        sub = (
            getattr(user, "sub", None)
            or getattr(user, "id", None)
            or getattr(user, "user_id", None)
        )

    return str(sub) if sub else None
