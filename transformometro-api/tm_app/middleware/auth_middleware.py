from __future__ import annotations

from fastapi import Request
from delpi_auth.middleware.fastapi_auth import jwt_middleware as _base_jwt_middleware
from delpi_auth.middleware.fastapi_auth import normalize_path
from delpi_auth.service_token import request_has_valid_internal_service_token

__all__ = ["jwt_middleware"]


def _is_engineering_integration_path(path: str) -> bool:
    normalized = normalize_path(path)
    return "integrations/engineering/transforma-mais" in normalized


async def jwt_middleware(request: Request, call_next):
    if _is_engineering_integration_path(request.url.path) and request_has_valid_internal_service_token(
        request
    ):
        return await call_next(request)

    return await _base_jwt_middleware(request, call_next)
