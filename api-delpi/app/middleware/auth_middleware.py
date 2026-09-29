# app/middleware/auth_middleware.py

from fastapi import Request

from delpi_auth.jwt_validator import validate_token
from delpi_auth.middleware.fastapi_auth import jwt_middleware as _base_jwt_middleware
from delpi_auth.service_token import request_has_valid_internal_service_token
from delpi_mcp.auth import (
    McpTransportAuthPolicy,
    is_mcp_data_path,
    mcp_transport_auth,
)

from app.interface.mcp.oauth_contract import (
    MCP_OAUTH_SCOPES,
    resolve_required_mcp_resource_audience,
)
from app.interface.mcp.resource_metadata import www_authenticate_challenge

__all__ = ["jwt_middleware", "_is_public_delpi_path"]

# Prefixos públicos (sem JWT) servidos pela api-delpi.
# Ex.: leitura pública da inspeção via QR (public-hub), protegida por token opaco.
_PUBLIC_PREFIXES = (
    "/public/quality-labels/",
    "/public/kaizen/",
    "/public/mural-acessos/",
    "/public/canal-denuncia/",
    "/public/scheduling/",
)

# Exact public paths (Custom GPT OpenAPI import only — no business data).
_PUBLIC_EXACT = frozenset(
    {
        "/gpt-actions/v1/openapi.json",
    }
)

# root_path possíveis (o gateway costuma remover, mas mantemos robustez).
_ROOT_PREFIXES = ("/apps/api-delpi",)


def _strip_root(path: str) -> str:
    for root in _ROOT_PREFIXES:
        if path.startswith(root):
            return path[len(root):] or "/"
    return path


def _is_oauth_metadata_path(normalized: str) -> bool:
    return normalized.startswith("/.well-known/oauth-protected-resource")


def _is_mcp_data_path(normalized: str) -> bool:
    return is_mcp_data_path(normalized)


def _is_public_delpi_path(path: str) -> bool:
    normalized = _strip_root(path.split("?", 1)[0])
    if normalized in _PUBLIC_EXACT:
        return True
    if _is_oauth_metadata_path(normalized):
        return True
    return any(normalized.startswith(prefix) for prefix in _PUBLIC_PREFIXES)


# S3: MCP transport AuthN policy (DAVI wire preserved — space-separated
# challenge, redecoration of a base-middleware 401 with the MCP challenge).
_MCP_TRANSPORT_POLICY = McpTransportAuthPolicy(
    resolve_resource_audience=resolve_required_mcp_resource_audience,
    required_scopes=MCP_OAUTH_SCOPES,
    challenge=www_authenticate_challenge,
    redecorate_base_401=True,
)


async def jwt_middleware(request: Request, call_next):
    if _is_public_delpi_path(request.url.path):
        return await call_next(request)

    normalized = _strip_root(request.url.path.split("?", 1)[0])
    if _is_mcp_data_path(normalized):
        # Auth model A: entire MCP transport requires user OAuth before tools/list.
        # Machine/service identity is forbidden on this user-data surface.
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
