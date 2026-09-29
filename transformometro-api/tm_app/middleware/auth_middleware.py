from __future__ import annotations

from fastapi import Request

from delpi_auth.jwt_validator import validate_token
from delpi_auth.middleware.fastapi_auth import jwt_middleware as _base_jwt_middleware
from delpi_auth.middleware.fastapi_auth import normalize_path
from delpi_auth.service_token import request_has_valid_internal_service_token
from delpi_mcp.auth import (
    McpTransportAuthPolicy,
    is_mcp_data_path,
    mcp_transport_auth,
)

from tm_app.interface.mcp.oauth_contract import (
    MCP_OAUTH_SCOPES,
    resolve_required_mcp_resource_audience,
)
from tm_app.interface.mcp.resource_metadata import www_authenticate_challenge

__all__ = ["jwt_middleware", "_is_public", "PUBLIC_PREFIXES", "PUBLIC_EXACT"]

PUBLIC_EXACT: frozenset[str] = frozenset(
    {
        "/health",
        "/transformometro/gpt-actions/v1/openapi.json",
    }
)
PUBLIC_PREFIXES: tuple[str, ...] = ("/public/",)


def _strip_root_path(request: Request) -> str:
    path = request.url.path
    root_path = (request.scope.get("root_path") or "").rstrip("/")
    if root_path and path.startswith(root_path):
        return path[len(root_path) :] or "/"
    return path


def _is_public(path: str) -> bool:
    normalized = normalize_path(path)
    if normalized in PUBLIC_EXACT or path in PUBLIC_EXACT:
        return True
    if normalized.startswith("/.well-known/oauth-protected-resource"):
        return True
    return any(
        normalized.startswith(prefix) or path.startswith(prefix)
        for prefix in PUBLIC_PREFIXES
    )


def _is_engineering_integration_path(path: str) -> bool:
    normalized = normalize_path(path)
    return "integrations/engineering/transforma-mais" in normalized


def _is_mcp_data_path(normalized: str) -> bool:
    return is_mcp_data_path(normalized)


# S3: MCP transport AuthN policy (TÉO wire preserved — space-separated
# challenge, redecoration of a base-middleware 401 with the MCP challenge).
_MCP_TRANSPORT_POLICY = McpTransportAuthPolicy(
    resolve_resource_audience=resolve_required_mcp_resource_audience,
    required_scopes=MCP_OAUTH_SCOPES,
    challenge=www_authenticate_challenge,
    redecorate_base_401=True,
)


async def jwt_middleware(request: Request, call_next):
    stripped = _strip_root_path(request)
    if _is_public(stripped):
        return await call_next(request)

    if _is_engineering_integration_path(request.url.path) and request_has_valid_internal_service_token(
        request
    ):
        return await call_next(request)

    normalized = normalize_path(stripped.split("?", 1)[0])
    if _is_mcp_data_path(normalized):
        # Transport-level OAuth: user JWT only; service tokens forbidden.
        # Business AuthZ remains application-owned downstream of delpi_auth.
        return await mcp_transport_auth(
            request,
            call_next,
            policy=_MCP_TRANSPORT_POLICY,
            token_validator=validate_token,
            service_token_gate=request_has_valid_internal_service_token,
            base_auth_middleware=_base_jwt_middleware,
        )

    return await _base_jwt_middleware(request, call_next)
