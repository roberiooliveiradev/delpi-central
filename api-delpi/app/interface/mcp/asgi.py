"""ASGI wiring for the API DELPI MCP Streamable HTTP surface."""

from __future__ import annotations

from contextlib import AsyncExitStack, asynccontextmanager
from collections.abc import AsyncIterator, Callable
from typing import Any

from starlette.applications import Starlette
from starlette.requests import Request

from app.interface.mcp.server import create_mcp_server

_mcp = create_mcp_server()
mcp_http_app: Starlette = _mcp.streamable_http_app()

# Canonical public resource is /apps/api-delpi/mcp (no trailing slash).
# FastAPI/Starlette Mount("/mcp") + streamable_http_path="/" otherwise issues
# HTTP 307 POST /mcp → /mcp/, which breaks ChatGPT MCP clients.
_MCP_EXACT_PATHS = frozenset({"/mcp", "/apps/api-delpi/mcp"})


def normalize_mcp_mount_path(path: str) -> str:
    """Map exact MCP mount paths to the trailing-slash form without redirect."""
    if path in _MCP_EXACT_PATHS:
        return f"{path}/"
    return path


async def mcp_mount_path_middleware(request: Request, call_next: Callable[..., Any]) -> Any:
    """Internal path rewrite so POST to the canonical MCP URL does not 307."""
    path = request.scope.get("path") or ""
    normalized = normalize_mcp_mount_path(path)
    if normalized != path:
        request.scope["path"] = normalized
        if "raw_path" in request.scope:
            request.scope["raw_path"] = normalized.encode("ascii")
    return await call_next(request)


def combine_lifespan(
    app_lifespan: Callable[..., Any],
    mcp_app: Starlette,
) -> Callable[..., Any]:
    """Run api-delpi lifespan together with the MCP session manager lifespan."""

    @asynccontextmanager
    async def combined(app: Any) -> AsyncIterator[None]:
        async with AsyncExitStack() as stack:
            await stack.enter_async_context(app_lifespan(app))
            await stack.enter_async_context(mcp_app.router.lifespan_context(mcp_app))
            yield

    return combined


__all__ = [
    "mcp_http_app",
    "combine_lifespan",
    "mcp_mount_path_middleware",
    "normalize_mcp_mount_path",
    "_mcp",
]
