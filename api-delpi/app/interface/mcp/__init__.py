"""API DELPI MCP interface (OpenAI Plugin adapter boundary)."""

from app.interface.mcp.asgi import combine_lifespan, mcp_http_app
from app.interface.mcp.routes import router as mcp_metadata_router

__all__ = ["combine_lifespan", "mcp_http_app", "mcp_metadata_router"]
