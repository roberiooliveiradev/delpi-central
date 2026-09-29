"""ASGI wiring for the API DELPI MCP Streamable HTTP surface."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from starlette.applications import Starlette

from delpi_mcp.transport import (
    combine_lifespans as _shared_combine_lifespans,
)
from delpi_mcp.transport import (
    mcp_mount_path_middleware as _shared_mount_middleware,
)
from delpi_mcp.transport import (
    normalize_mcp_mount_path as _shared_normalize_path,
)

from app.interface.mcp.server import create_mcp_server

_mcp = create_mcp_server()
mcp_http_app: Starlette = _mcp.streamable_http_app()

# Canonical public resource is /apps/api-delpi/mcp (no trailing slash).
# FastAPI/Starlette Mount("/mcp") + streamable_http_path="/" otherwise issues
# HTTP 307 POST /mcp → /mcp/, which breaks ChatGPT MCP clients.
_MCP_EXACT_PATHS = frozenset({"/mcp", "/apps/api-delpi/mcp"})


def normalize_mcp_mount_path(path: str) -> str:
    """Map exact MCP mount paths to the trailing-slash form without redirect."""
    return _shared_normalize_path(path, _MCP_EXACT_PATHS)


mcp_mount_path_middleware = _shared_mount_middleware(_MCP_EXACT_PATHS)


def combine_lifespan(
    app_lifespan: Callable[..., Any],
    mcp_app: Starlette,
) -> Callable[..., Any]:
    """Run api-delpi lifespan together with the MCP session manager lifespan."""
    return _shared_combine_lifespans(
        app_lifespan,
        lambda _app: mcp_app.router.lifespan_context(mcp_app),
    )


__all__ = [
    "mcp_http_app",
    "combine_lifespan",
    "mcp_mount_path_middleware",
    "normalize_mcp_mount_path",
    "_mcp",
]
