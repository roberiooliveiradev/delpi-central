# app/middleware/auth_middleware.py

from fastapi import Request
from fastapi.responses import JSONResponse

from delpi_auth.middleware.fastapi_auth import jwt_middleware as _base_jwt_middleware
from delpi_auth.service_token import request_has_valid_internal_service_token

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


def _unauthorized_mcp() -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={"detail": "Unauthorized"},
        headers={"WWW-Authenticate": www_authenticate_challenge()},
    )


async def jwt_middleware(request: Request, call_next):
    if _is_public_delpi_path(request.url.path):
        return await call_next(request)

    normalized = _strip_root(request.url.path.split("?", 1)[0])
    if _is_mcp_data_path(normalized):
        # User-data MCP surface: machine/service identity is forbidden.
        if request_has_valid_internal_service_token(request):
            return _unauthorized_mcp()
        response = await _base_jwt_middleware(request, call_next)
        if getattr(response, "status_code", None) == 401:
            response.headers["WWW-Authenticate"] = www_authenticate_challenge()
        return response

    return await _base_jwt_middleware(request, call_next)
