# app/middleware/auth_middleware.py

from fastapi import Request
from fastapi.responses import JSONResponse

from delpi_auth.jwt_validator import validate_token
from delpi_auth.middleware.fastapi_auth import jwt_middleware as _base_jwt_middleware
from delpi_auth.service_token import request_has_valid_internal_service_token

from app.interface.mcp.oauth_contract import missing_required_oauth_scopes
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
    return normalized == "/mcp" or normalized.startswith("/mcp/")


def _is_public_delpi_path(path: str) -> bool:
    normalized = _strip_root(path.split("?", 1)[0])
    if normalized in _PUBLIC_EXACT:
        return True
    if _is_oauth_metadata_path(normalized):
        return True
    return any(normalized.startswith(prefix) for prefix in _PUBLIC_PREFIXES)


def _unauthorized_mcp(
    *,
    error: str = "invalid_token",
    error_description: str = "Authentication required",
) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={"detail": "Unauthorized"},
        headers={
            "WWW-Authenticate": www_authenticate_challenge(
                error=error,
                error_description=error_description,
            )
        },
    )


async def jwt_middleware(request: Request, call_next):
    if _is_public_delpi_path(request.url.path):
        return await call_next(request)

    normalized = _strip_root(request.url.path.split("?", 1)[0])
    if _is_mcp_data_path(normalized):
        # Auth model A: entire MCP transport requires user OAuth before tools/list.
        # Machine/service identity is forbidden on this user-data surface.
        if request_has_valid_internal_service_token(request):
            return _unauthorized_mcp(
                error="invalid_token",
                error_description="User authentication required",
            )

        auth_header = request.headers.get("Authorization") or ""
        if not auth_header.startswith("Bearer "):
            return _unauthorized_mcp()

        token = auth_header.split(" ", 1)[1].strip()
        if not token:
            return _unauthorized_mcp()

        try:
            # Platform JWT verification (signature/issuer/exp/nbf/aud=KEYCLOAK_AUDIENCE).
            # MCP resource URL audience (RFC 8707) is NOT assumed; see oauth evidence doc.
            claims = validate_token(token)
            missing = missing_required_oauth_scopes(claims)
            if missing:
                return _unauthorized_mcp(
                    error="insufficient_scope",
                    error_description="Required OAuth scopes are missing",
                )
        except Exception:
            return _unauthorized_mcp(
                error="invalid_token",
                error_description="Access token validation failed",
            )

        response = await _base_jwt_middleware(request, call_next)
        if getattr(response, "status_code", None) == 401:
            response.headers["WWW-Authenticate"] = www_authenticate_challenge(
                error="invalid_token",
                error_description="Authentication required",
            )
        return response

    return await _base_jwt_middleware(request, call_next)
