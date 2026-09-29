"""Shared MCP identity / request-context bridge (S4).

Owns ONLY the read-side bridge duplicated across VISTA/TÉO/DAVI:

- snapshot of the identity context already established by ``delpi_auth``
  (``request_context`` ContextVars populated by the S3-authenticated HTTP
  middleware);
- fail-closed accessor that refuses to proceed without a validated user;
- reconstruction of a minimal Starlette ``Request`` for application
  adapters that consume ``request.state.user`` / the original
  ``Authorization`` header.

This module performs NO authentication: it never validates JWT, checks
audience/scopes, loads RBAC or queries Keycloak/Core. It only transports
the already-validated context — interpreting permissions is forbidden.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from starlette.requests import Request

from delpi_auth.request_context import (
    get_current_user,
    get_request_authorization,
)

__all__ = [
    "McpRequestContext",
    "build_mcp_request",
    "current_mcp_context",
    "require_mcp_context",
]


@dataclass(frozen=True)
class McpRequestContext:
    """Domain-neutral snapshot of the authenticated MCP caller context.

    ``user`` is the canonical object placed on the ``delpi_auth`` ContextVar
    (same instance ``request.state.user`` receives) — carried opaquely,
    never interpreted. ``authorization`` is the original Authorization
    header value, pass-through only (never logged, never persisted, never
    placed in tool results or prompts).
    """

    user: Any
    authorization: str


def current_mcp_context() -> McpRequestContext:
    """Read-only snapshot of the current delpi_auth-established context.

    ``user`` may be ``None`` when no identity context exists — the caller
    decides whether that is acceptable (identity-only consumers may need
    only the authorization value).
    """
    return McpRequestContext(
        user=get_current_user(),
        authorization=(get_request_authorization() or "").strip(),
    )


def require_mcp_context() -> McpRequestContext:
    """Snapshot that fails closed when no validated user context exists.

    Raises ``PermissionError("Unauthorized")`` — the same failure shape the
    per-app bridges already produced, mapped by their error adapters to the
    canonical unauthenticated tool result.
    """
    context = current_mcp_context()
    if context.user is None:
        raise PermissionError("Unauthorized")
    return context


def build_mcp_request(
    *,
    context: McpRequestContext,
    server: tuple[str, int],
    client: tuple[str, int],
    extra_headers: Mapping[str, str] | None = None,
) -> Request:
    """Rebuild the minimal Starlette Request adapters consume.

    Only fields actually read downstream are reconstructed: the
    ``authorization`` header (plus optional per-app headers such as
    ``mcp-context``) and ``request.state.user`` — the exact same object the
    ``delpi_auth`` ContextVar holds. This is not a fake browser request and
    carries no identity beyond the already-validated context.
    """
    headers: dict[str, str] = {}
    if context.authorization:
        headers["authorization"] = context.authorization
    if extra_headers:
        headers.update(extra_headers)
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "https",
        "path": "/mcp",
        "raw_path": b"/mcp",
        "query_string": b"",
        "headers": [
            (k.lower().encode("latin-1"), v.encode("latin-1"))
            for k, v in headers.items()
        ],
        "client": client,
        "server": server,
        "state": {},
    }
    request = Request(scope)
    request.state.user = context.user
    return request
