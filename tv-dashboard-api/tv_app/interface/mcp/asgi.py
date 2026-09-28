"""ASGI glue: mount FastMCP streamable-http at /mcp without redirect regressions.

Clients MUST be able to POST to the canonical `/mcp` (no trailing slash).
Starlette mounting `/mcp` only matches `/mcp/`; posting to `/mcp` yields a
307 that some OAuth providers reject. We therefore rewrite the path in a tiny
middleware on the outer FastAPI app before router resolution (same proven
pattern as TÉO/DAVI).
"""

from __future__ import annotations

import contextlib
from collections.abc import AsyncIterator, Callable
from typing import Any

from fastapi import FastAPI, Request
from mcp.server.fastmcp import FastMCP
from starlette.types import ASGIApp

_MCP_EXACT_PATHS = {"/mcp", "/apps/tv-dashboard-api/mcp"}


def mcp_http_app(mcp: FastMCP) -> ASGIApp:
    """Streamable HTTP ASGI app (`streamable_http_path="/"`)."""
    return mcp.streamable_http_app()


def combine_lifespan(app: FastAPI, mcp: FastMCP) -> None:
    """Compose existing FastAPI lifespan with FastMCP session/task-group lifespan."""
    original = app.router.lifespan_context

    @contextlib.asynccontextmanager
    async def combined(a: FastAPI) -> AsyncIterator[dict]:
        async with original(a):
            async with mcp.session_manager.run():
                yield {}

    app.router.lifespan_context = combined


async def mcp_mount_path_middleware(request: Request, call_next: Callable[..., Any]) -> Any:
    """Internal path rewrite so POST to the canonical MCP URL does not 307.

    Registered via ``app.middleware("http")`` — runs before route/mount
    resolution; `/mcp` → `/mcp/` (and the gateway-prefixed variant) so the
    Streamable HTTP mount matches without emitting a redirect.
    """
    path = request.scope.get("path") or ""
    if path in _MCP_EXACT_PATHS:
        normalized = path + "/"
        request.scope["path"] = normalized
        if "raw_path" in request.scope:
            request.scope["raw_path"] = normalized.encode("ascii")
    return await call_next(request)
