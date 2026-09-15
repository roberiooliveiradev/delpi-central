"""HTTP routes for MCP OAuth Protected Resource Metadata (public)."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.interface.mcp.resource_metadata import build_oauth_protected_resource_metadata

router = APIRouter(tags=["API DELPI MCP OAuth Metadata"])


@router.get(
    "/.well-known/oauth-protected-resource",
    include_in_schema=False,
    operation_id="mcp_oauth_protected_resource_metadata",
)
def oauth_protected_resource_metadata():
    return JSONResponse(build_oauth_protected_resource_metadata())


@router.get(
    "/.well-known/oauth-protected-resource/mcp",
    include_in_schema=False,
    operation_id="mcp_oauth_protected_resource_metadata_path",
)
def oauth_protected_resource_metadata_path():
    return JSONResponse(build_oauth_protected_resource_metadata())
