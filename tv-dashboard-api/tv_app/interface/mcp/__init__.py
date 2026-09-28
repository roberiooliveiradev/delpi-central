"""MCP adapter surface for TV Dashboard (VISTA) — READ tools only (MCP1)."""

from .asgi import combine_lifespan, mcp_http_app, mcp_mount_path_middleware
from .routes import mcp_metadata_router
from .server import create_mcp_server

__all__ = [
    "combine_lifespan",
    "create_mcp_server",
    "mcp_http_app",
    "mcp_metadata_router",
    "mcp_mount_path_middleware",
]
