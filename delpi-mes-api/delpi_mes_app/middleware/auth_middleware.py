from __future__ import annotations

from fastapi import Request

from delpi_auth.middleware.fastapi_auth import jwt_middleware as _base_jwt_middleware
from delpi_auth.middleware.fastapi_auth import normalize_path


def _is_public_health(path: str) -> bool:
    normalized = normalize_path(path)
    return normalized == "/health" or normalized.endswith("/delpi-mes-api/health")


async def jwt_middleware(request: Request, call_next):
    if _is_public_health(request.url.path):
        return await call_next(request)
    return await _base_jwt_middleware(request, call_next)
