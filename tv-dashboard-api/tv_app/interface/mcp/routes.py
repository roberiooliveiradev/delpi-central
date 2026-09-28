"""HTTP routes that complement the FastMCP mount (OAuth discovery only)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .resource_metadata import build_protected_resource_document

logger = logging.getLogger(__name__)

mcp_metadata_router = APIRouter()


@mcp_metadata_router.get("/.well-known/oauth-protected-resource")
@mcp_metadata_router.get("/.well-known/oauth-protected-resource/apps/tv-dashboard-api/mcp")
async def oauth_protected_resource_metadata(request: Request) -> JSONResponse:
    """RFC 9728 Protected Resource Metadata (public, no JWT)."""
    base = str(request.base_url).rstrip("/")
    try:
        body = build_protected_resource_document(base)
        return JSONResponse(body)
    except Exception as exc:
        logger.warning("oauth-protected-resource metadata failed: %s", type(exc).__name__)
        return JSONResponse({"error": "metadata_unavailable"}, status_code=503)
