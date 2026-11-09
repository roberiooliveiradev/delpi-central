"""Request-scoped actorClientId for realtime anti-echo (ContextVar)."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

_actor_client_id: ContextVar[str | None] = ContextVar(
    "tm_realtime_actor_client_id", default=None
)


def get_realtime_actor_client_id() -> str | None:
    value = _actor_client_id.get()
    return str(value).strip() or None if value else None


@contextmanager
def realtime_actor_client_id(client_id: str | None) -> Iterator[None]:
    token = _actor_client_id.set(str(client_id).strip() if client_id else None)
    try:
        yield
    finally:
        _actor_client_id.reset(token)
