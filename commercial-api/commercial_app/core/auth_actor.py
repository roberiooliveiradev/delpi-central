from __future__ import annotations

import re
from contextvars import ContextVar

from fastapi import Request

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

_actor_display_name: ContextVar[str | None] = ContextVar(
    "commercial_actor_display_name",
    default=None,
)
_actor_client_id: ContextVar[str | None] = ContextVar(
    "commercial_actor_client_id",
    default=None,
)


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


def _safe_display_label(value: str | None) -> str | None:
    cleaned = (value or "").strip()
    if not cleaned or _UUID_RE.match(cleaned):
        return None
    return cleaned


def actor_sub_from_request(request: Request) -> str | None:
    user = getattr(request.state, "user", None)
    if user is None:
        return None
    return _user_attr(user, "sub", "id", "user_id")


def current_user_from_request(request: Request):
    return getattr(request.state, "user", None)


def actor_display_name_from_request(request: Request) -> str | None:
    """
    Nome amigável do ator autenticado (RBAC/JWT), nunca UUID cru.
    Preferência: name → preferred_username → email.
    """
    user = current_user_from_request(request)
    if user is None:
        return None
    for key in ("name", "preferred_username", "email"):
        label = _safe_display_label(_user_attr(user, key))
        if label:
            return label
    return None


def peek_actor_display_name() -> str | None:
    return _actor_display_name.get()


def peek_actor_client_id() -> str | None:
    return _actor_client_id.get()


def bind_request_actor(request: Request) -> None:
    """Propaga nome/clientId do request até `_append_audit` / notify realtime.

    Deve ser chamada **dentro do contexto da requisição** (middleware http):
    os valores ficam no ContextVar do contexto corrente, herdado pelo handler
    e pelos use cases. Não usa `reset()` — a dependência sync com `yield` que
    fazia isso quebrava (`ValueError: Token created in a different Context`)
    porque enter/exit de dependências FastAPI rodam em contextos distintos.
    Como cada requisição executa em contexto próprio, o valor não vaza entre
    requisições concorrentes.
    """
    from commercial_app.interface.http.client_id import client_id_from_request

    _actor_display_name.set(actor_display_name_from_request(request))
    _actor_client_id.set(client_id_from_request(request))
