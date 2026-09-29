"""Shared MCP ASGI/transport glue (S2).

Owns ONLY the duplicated transport-runtime mechanics proven identical
across VISTA, TÉO and DAVI:

- canonical ``/mcp`` → ``/mcp/`` ASGI path rewrite (no HTTP 307/308);
- deterministic lifespan composition (app lifespan + MCP lifespan);
- the ``TransportSecuritySettings`` shape with DNS-rebinding protection
  always enabled (hosts/origins stay per-app — see ``resource_contract``
  for the TÉO/DAVI derivation and VISTA's env-driven allowlist).

Deliberately NOT shared (Abstraction Gate):

- server/streamable-app construction — ``MCPServer`` construction is
  app-local; a shared adapter would become a server factory, which the
  design freeze forbids;
- tool registration, bridges, dispatch, domain services;
- auth middleware ordering/semantics (S1/S3 boundary).

The helpers below are plain ASGI/Python — they do not import SDK server
types (``mcp_transport_security_settings`` lazy-imports the SDK settings
type only inside the function).
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable, Container
from contextlib import AsyncExitStack, asynccontextmanager
from typing import Any

__all__ = [
    "combine_lifespans",
    "mcp_mount_path_middleware",
    "mcp_transport_security_settings",
    "normalize_mcp_mount_path",
]


def normalize_mcp_mount_path(path: str, exact_paths: Container[str]) -> str:
    """Map an exact canonical MCP path to its trailing-slash mount form.

    Exact match only — ``/mcp/`` and ``/mcp/<sub>`` are untouched, as are
    all unrelated paths.
    """
    if path in exact_paths:
        return f"{path}/"
    return path


def mcp_mount_path_middleware(
    exact_paths: Container[str],
) -> Callable[..., Any]:
    """Starlette ``app.middleware("http")``-style path rewrite.

    Rewrites ``scope["path"]``/``scope["raw_path"]`` for the exact canonical
    paths before route/mount resolution so POST to slashless ``/mcp``
    reaches the streamable-HTTP mount without a 307/308. Preserves method,
    headers, query string, body, root_path and client/server scope fields —
    and produces no response itself (auth stays downstream).
    """

    async def _middleware(request: Any, call_next: Callable[..., Any]) -> Any:
        path = request.scope.get("path") or ""
        normalized = normalize_mcp_mount_path(path, exact_paths)
        if normalized != path:
            request.scope["path"] = normalized
            if "raw_path" in request.scope:
                request.scope["raw_path"] = normalized.encode("ascii")
        return await call_next(request)

    return _middleware


def combine_lifespans(
    *lifespans: Callable[[Any], Any], yield_state: Any = None
) -> Callable[[Any], Any]:
    """Compose ASGI lifespans in order (deterministic startup/shutdown).

    Each entry is a ``(app) -> async context manager`` callable; the MCP
    session-manager side can be wrapped as ``lambda _app: <cm>``. Entries
    start in order and unwind in reverse via ``AsyncExitStack``; startup
    and shutdown exceptions propagate unchanged.

    ``yield_state`` preserves per-app yield contracts (VISTA yields ``{}``,
    TÉO/DAVI yield ``None``).
    """

    @asynccontextmanager
    async def combined(app: Any) -> AsyncIterator[Any]:
        async with AsyncExitStack() as stack:
            for lifespan in lifespans:
                await stack.enter_async_context(lifespan(app))
            yield yield_state

    return combined


def mcp_transport_security_settings(
    *,
    allowed_hosts: "list[str] | tuple[str, ...]",
    allowed_origins: "list[str] | tuple[str, ...]",
) -> Any:
    """SDK ``TransportSecuritySettings`` with DNS-rebinding protection on.

    Host/origin allowlists remain app-owned inputs (VISTA env allowlist;
    TÉO/DAVI ``mcp_allowed_hosts_and_origins``). This helper only fixes the
    common settings shape so no app can silently disable protection.
    """
    from mcp.server.transport_security import TransportSecuritySettings

    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=list(allowed_hosts),
        allowed_origins=list(allowed_origins),
    )
