"""ASGI wiring for Transformômetro MCP Streamable HTTP."""

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

from tm_app.interface.mcp.server import create_mcp_server, teo_mcp_transport_security

_mcp = create_mcp_server()
mcp_http_app: Starlette = _mcp.streamable_http_app(
    streamable_http_path="/",
    json_response=True,
    stateless_http=True,
    transport_security=teo_mcp_transport_security(),
)

_MCP_EXACT_PATHS = frozenset(
    {
        "/mcp",
        "/apps/transformometro-api/mcp",
    }
)


def normalize_mcp_mount_path(path: str) -> str:
    return _shared_normalize_path(path, _MCP_EXACT_PATHS)


mcp_mount_path_middleware = _shared_mount_middleware(_MCP_EXACT_PATHS)


def combine_lifespan(
    app_lifespan: Callable[..., Any],
    mcp_app: Starlette,
) -> Callable[..., Any]:
    return _shared_combine_lifespans(
        app_lifespan,
        lambda _app: mcp_app.router.lifespan_context(mcp_app),
    )


__all__ = [
    "combine_lifespan",
    "mcp_http_app",
    "mcp_mount_path_middleware",
    "normalize_mcp_mount_path",
    "_mcp",
]
