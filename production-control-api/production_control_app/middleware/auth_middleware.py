"""JWT do Portal PCP — health e cockpit do operador públicos mesmo com ASGI root_path."""

from __future__ import annotations

from fastapi import Request

from delpi_auth.middleware.fastapi_auth import jwt_middleware as _base_jwt_middleware
from delpi_auth.middleware.fastapi_auth import normalize_path

__all__ = ["jwt_middleware"]


def _is_public_health(path: str) -> bool:
    normalized = normalize_path(path)
    if normalized == "/health":
        return True
    # uvicorn --root-path /apps/production-control-api → path completo no middleware
    return normalized.endswith("/production-control-api/health")


def _is_public_route(path: str) -> bool:
    """Rotas do cockpit do operador — link aberto, somente leitura."""
    normalized = normalize_path(path)
    return normalized.startswith("/public/") or "/production-control-api/public/" in normalized


async def jwt_middleware(request: Request, call_next):
    path = request.url.path
    if _is_public_health(path) or _is_public_route(path):
        return await call_next(request)
    return await _base_jwt_middleware(request, call_next)
