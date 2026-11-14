"""Token do pedido, só em memória. Não entra no banco nem em log."""

from __future__ import annotations

from contextvars import ContextVar

_tokens: dict[str, str] = {}
current_bearer: ContextVar[str] = ContextVar("entry_audit_bearer", default="")


def remember_bearer(analysis_id: str, token: str) -> None:
    if analysis_id and token:
        _tokens[analysis_id] = token


def bearer_for(analysis_id: str) -> str:
    return _tokens.get(analysis_id, "")
