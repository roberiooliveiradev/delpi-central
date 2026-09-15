"""ASGI wiring for the API DELPI MCP Streamable HTTP surface."""

from __future__ import annotations

from contextlib import AsyncExitStack, asynccontextmanager
from collections.abc import AsyncIterator, Callable
from typing import Any

from starlette.applications import Starlette

from app.interface.mcp.server import create_mcp_server

_mcp = create_mcp_server()
mcp_http_app: Starlette = _mcp.streamable_http_app()


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


__all__ = ["mcp_http_app", "combine_lifespan", "_mcp"]
