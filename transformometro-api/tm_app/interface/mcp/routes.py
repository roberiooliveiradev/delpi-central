"""HTTP routes for Transformômetro MCP OAuth Protected Resource Metadata."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from tm_app.interface.mcp.resource_metadata import build_oauth_protected_resource_metadata

router = APIRouter(tags=["Transformômetro MCP OAuth Metadata"])


@router.get(
    "/.well-known/oauth-protected-resource",
    include_in_schema=False,
    operation_id="tm_mcp_oauth_protected_resource_metadata",
)
def oauth_protected_resource_metadata():
    return JSONResponse(build_oauth_protected_resource_metadata())


@router.get(
    "/.well-known/oauth-protected-resource/mcp",
    include_in_schema=False,
    operation_id="tm_mcp_oauth_protected_resource_metadata_path",
)
def oauth_protected_resource_metadata_path():
    return JSONResponse(build_oauth_protected_resource_metadata())
