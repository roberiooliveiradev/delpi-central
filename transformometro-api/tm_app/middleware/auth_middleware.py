from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from delpi_auth.jwt_validator import validate_token
from delpi_auth.middleware.fastapi_auth import jwt_middleware as _base_jwt_middleware
from delpi_auth.middleware.fastapi_auth import normalize_path
from delpi_auth.service_token import request_has_valid_internal_service_token

from tm_app.interface.mcp.oauth_contract import (
    missing_required_oauth_scopes,
    resolve_required_mcp_resource_audience,
    token_has_exact_audience,
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
    return normalized == "/mcp" or normalized.startswith("/mcp/")


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
            claims = validate_token(token)
            mcp_resource = resolve_required_mcp_resource_audience()
            if not token_has_exact_audience(claims, mcp_resource):
                return _unauthorized_mcp(
                    error="invalid_token",
                    error_description="MCP resource audience is required",
                )
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
