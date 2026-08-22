"""JWT do Portal Financeiro — health público mesmo com ASGI root_path."""

from __future__ import annotations

from fastapi import Request

from delpi_auth.middleware.fastapi_auth import jwt_middleware as _base_jwt_middleware
from delpi_auth.middleware.fastapi_auth import normalize_path

__all__ = ["jwt_middleware"]


def _is_public_health(path: str) -> bool:
    normalized = normalize_path(path)
    if normalized == "/health":
        return True
    # uvicorn --root-path /apps/financial-api → path completo no middleware
    return normalized.endswith("/financial-api/health")


async def jwt_middleware(request: Request, call_next):
    if _is_public_health(request.url.path):
        return await call_next(request)
    return await _base_jwt_middleware(request, call_next)
