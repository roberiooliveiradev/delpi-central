"""CLARA — MCP interface (especialista Controladoria & Finanças)."""

from controllership_finance_app.interface.mcp.asgi import (
    combine_lifespan,
    mcp_http_app,
    mcp_mount_path_middleware,
)
from controllership_finance_app.interface.mcp.routes import (
    router as mcp_metadata_router,
)

__all__ = [
    "combine_lifespan",
    "mcp_http_app",
    "mcp_metadata_router",
    "mcp_mount_path_middleware",
]
