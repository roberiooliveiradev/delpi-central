from __future__ import annotations

from fastapi import Request
from delpi_auth.middleware.fastapi_auth import jwt_middleware as _base_jwt_middleware
from delpi_auth.middleware.fastapi_auth import normalize_path
from delpi_auth.service_token import request_has_valid_internal_service_token

__all__ = ["jwt_middleware", "_is_public", "PUBLIC_PREFIXES", "PUBLIC_EXACT"]

PUBLIC_EXACT: frozenset[str] = frozenset({"/health"})
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
    return any(
        normalized.startswith(prefix) or path.startswith(prefix)
        for prefix in PUBLIC_PREFIXES
    )


def _is_engineering_integration_path(path: str) -> bool:
    normalized = normalize_path(path)
    return "integrations/engineering/transforma-mais" in normalized


async def jwt_middleware(request: Request, call_next):
    if _is_public(_strip_root_path(request)):
        return await call_next(request)

    if _is_engineering_integration_path(request.url.path) and request_has_valid_internal_service_token(
        request
    ):
        return await call_next(request)

    return await _base_jwt_middleware(request, call_next)
