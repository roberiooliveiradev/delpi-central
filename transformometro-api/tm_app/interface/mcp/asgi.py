"""ASGI wiring for Transformômetro MCP Streamable HTTP."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import AsyncExitStack, asynccontextmanager
from typing import Any

from starlette.applications import Starlette
from starlette.requests import Request

from tm_app.interface.mcp.server import create_mcp_server

_mcp = create_mcp_server()
mcp_http_app: Starlette = _mcp.streamable_http_app()

_MCP_EXACT_PATHS = frozenset(
    {
        "/mcp",
        "/apps/transformometro-api/mcp",
    }
)


def normalize_mcp_mount_path(path: str) -> str:
    if path in _MCP_EXACT_PATHS:
        return f"{path}/"
    return path


async def mcp_mount_path_middleware(request: Request, call_next: Callable[..., Any]) -> Any:
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
    @asynccontextmanager
    async def combined(app: Any) -> AsyncIterator[None]:
        async with AsyncExitStack() as stack:
            await stack.enter_async_context(app_lifespan(app))
            await stack.enter_async_context(mcp_app.router.lifespan_context(mcp_app))
            yield

    return combined


__all__ = [
    "combine_lifespan",
    "mcp_http_app",
    "mcp_mount_path_middleware",
    "normalize_mcp_mount_path",
    "_mcp",
]
