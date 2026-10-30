"""SURI MCP ASGI app — sibling adapter process (ADR ARCH-MCP-01).

Standalone FastAPI app serving ONLY: the MCP Streamable HTTP transport
(``/mcp``), the public RFC 9728 protected-resource metadata and a health
endpoint. No Flask business surface is exposed by this process; tools
call the same gateways/policies in-process.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from delpi_mcp.transport import (
    combine_lifespans,
    mcp_mount_path_middleware as _shared_mount_middleware,
)
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.applications import Starlette

from app.interfaces.mcp.middleware import jwt_middleware
from app.interfaces.mcp.routes import router as mcp_metadata_router
from app.interfaces.mcp.server import (
    create_mcp_server,
    suri_mcp_transport_security,
)

_mcp = create_mcp_server()
mcp_http_app: Starlette = _mcp.streamable_http_app(
    streamable_http_path="/",
    json_response=True,
    stateless_http=True,
    transport_security=suri_mcp_transport_security(),
)

_MCP_EXACT_PATHS = frozenset({"/mcp"})

mcp_mount_mw = _shared_mount_middleware(_MCP_EXACT_PATHS)


@asynccontextmanager
async def _app_lifespan(_app: Any) -> AsyncIterator[None]:
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="SURI — Supplies MCP",
        description=(
            "Conversational MCP adapter of supplies-api (read-only v1). "
            "Business data flows through the same BFF contracts and "
            "AuthZ as the Portal Suprimentos."
        ),
        version="1.0.0",
        redirect_slashes=False,
        lifespan=combine_lifespans(
            _app_lifespan,
            lambda _app: mcp_http_app.router.lifespan_context(mcp_http_app),
        ),
    )

    @app.get("/healthz", include_in_schema=False)
    async def healthz() -> JSONResponse:
        return JSONResponse({"status": "ok", "service": "supplies-mcp"})

    app.middleware("http")(jwt_middleware)
    # Last registered runs first: rewrite /mcp → /mcp/ before Mount 307.
    app.middleware("http")(mcp_mount_mw)

    app.include_router(mcp_metadata_router)
    app.mount("/mcp", mcp_http_app)
    return app


app = create_app()
