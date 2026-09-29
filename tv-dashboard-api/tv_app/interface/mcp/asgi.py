"""ASGI glue: mount FastMCP streamable-http at /mcp without redirect regressions.

Clients MUST be able to POST to the canonical `/mcp` (no trailing slash).
Starlette mounting `/mcp` only matches `/mcp/`; posting to `/mcp` yields a
307 that some OAuth providers reject. We therefore rewrite the path in a tiny
middleware on the outer FastAPI app before router resolution (same proven
pattern as TÉO/DAVI).
"""

from __future__ import annotations

from fastapi import FastAPI
from mcp.server.mcpserver import MCPServer

from delpi_mcp.transport import (
    combine_lifespans as _shared_combine_lifespans,
)
from delpi_mcp.transport import (
    mcp_mount_path_middleware as _shared_mount_middleware,
)

from .server import mcp_transport_security
from starlette.types import ASGIApp

_MCP_EXACT_PATHS = frozenset({"/mcp", "/apps/tv-dashboard-api/mcp"})


def mcp_http_app(mcp: MCPServer) -> ASGIApp:
    """Streamable HTTP ASGI app (`streamable_http_path="/"`)."""
    return mcp.streamable_http_app(
        streamable_http_path="/",
        json_response=True,
        stateless_http=True,
        transport_security=mcp_transport_security(),
    )


def combine_lifespan(app: FastAPI, mcp: MCPServer) -> None:
    """Compose existing FastAPI lifespan with the MCP session/task-group lifespan."""
    app.router.lifespan_context = _shared_combine_lifespans(
        app.router.lifespan_context,
        lambda _app: mcp.session_manager.run(),
        yield_state={},
    )


mcp_mount_path_middleware = _shared_mount_middleware(_MCP_EXACT_PATHS)
