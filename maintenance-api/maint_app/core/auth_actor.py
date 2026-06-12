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
    """Extrai o identificador do usuário autenticado (sub / id do RBAC)."""
    user = getattr(request.state, "user", None)
    if user is None:
        return None
    return _user_attr(user, "sub", "id", "user_id")


def actor_nome_from_request(request: Request) -> str | None:
    """Nome de exibição do usuário (RBAC ou claims JWT)."""
    user = getattr(request.state, "user", None)
    if user is None:
        return None
    name = _user_attr(user, "name")
    if name and name.strip():
        return name.strip()
    email = _user_attr(user, "email")
    if email and email.strip():
        return email.strip()
    return None
