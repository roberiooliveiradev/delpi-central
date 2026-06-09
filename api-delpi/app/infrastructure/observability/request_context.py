"""Contexto da requisição HTTP para telemetria SQL (operation id, caller app)."""

from __future__ import annotations

from contextvars import ContextVar, Token

from fastapi import Request

_operation_id: ContextVar[str | None] = ContextVar("api_delpi_operation_id", default=None)
_caller_app: ContextVar[str | None] = ContextVar("api_delpi_caller_app", default=None)


def _resolve_operation_id(request: Request) -> str | None:
    route = request.scope.get("route")
    if route is None:
        return None

    operation_id = getattr(route, "operation_id", None)
    if isinstance(operation_id, str) and operation_id.strip():
        return operation_id.strip()

    return None


def bind_request_context(request: Request) -> tuple[Token, Token]:
    operation_token = _operation_id.set(_resolve_operation_id(request))
    caller_header = request.headers.get("X-Delpi-Caller-App")
    caller_token = _caller_app.set(caller_header.strip() if caller_header else None)
    return operation_token, caller_token


def reset_request_context(tokens: tuple[Token, Token]) -> None:
    operation_token, caller_token = tokens
    _operation_id.reset(operation_token)
    _caller_app.reset(caller_token)


def get_operation_id() -> str | None:
    return _operation_id.get()


def get_caller_app() -> str | None:
    return _caller_app.get()
