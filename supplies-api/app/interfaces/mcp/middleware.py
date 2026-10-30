"""SURI MCP transport auth middleware (S3).

The MCP adapter only serves the MCP data surface, the public
protected-resource metadata and health — every non-public path goes
through ``mcp_transport_auth`` (service-token ban, Bearer, JWT, exact
audience, required scopes) which then delegates to the canonical
``delpi_auth`` jwt_middleware for RBAC context loading.

Business AuthZ never lives here — tools re-apply the same
``can_use_operations``/``require_units`` policies the Flask routes use.
"""

from __future__ import annotations

from delpi_auth.jwt_validator import validate_token
from delpi_auth.middleware.fastapi_auth import (
    is_public_path,
    jwt_middleware as _base_jwt_middleware,
    normalize_path,
)
from delpi_auth.service_token import (
    request_has_valid_internal_service_token,
)
from delpi_mcp.auth import (
    McpTransportAuthPolicy,
    is_mcp_data_path,
    mcp_transport_auth,
)

from app.interfaces.mcp.oauth_contract import (
    MCP_OAUTH_SCOPES,
    resolve_required_mcp_resource_audience,
)
from app.interfaces.mcp.resource_metadata import (
    www_authenticate_challenge as _mcp_challenge,
)

__all__ = ["jwt_middleware"]

_MCP_TRANSPORT_POLICY = McpTransportAuthPolicy(
    resolve_resource_audience=resolve_required_mcp_resource_audience,
    required_scopes=MCP_OAUTH_SCOPES,
    challenge=_mcp_challenge,
    redecorate_base_401=True,
)


def _is_suri_public_path(path: str) -> bool:
    if is_public_path(path):
        return True
    normalized = normalize_path(path)
    if normalized in {"/healthz", "/ready", "/health"}:
        return True
    return normalized.startswith("/.well-known/oauth-protected-resource")


async def jwt_middleware(request, call_next):
    if _is_suri_public_path(request.url.path):
        return await call_next(request)
    normalized = normalize_path(request.url.path)
    if is_mcp_data_path(normalized):
        return await mcp_transport_auth(
            request,
            call_next,
            policy=_MCP_TRANSPORT_POLICY,
            token_validator=validate_token,
            service_token_gate=request_has_valid_internal_service_token,
            base_auth_middleware=_base_jwt_middleware,
        )
    return await _base_jwt_middleware(request, call_next)
