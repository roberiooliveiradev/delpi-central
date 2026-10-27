from delpi_auth.middleware.fastapi_auth import (
    is_public_path,
    jwt_middleware as _base_jwt_middleware,
    normalize_path,
)

__all__ = ["jwt_middleware"]

_PUBLIC_EXACT = {"/health", "/ready"}
_PUBLIC_SUFFIXES = (
    "/engineering-api/health",
    "/engineering-api/ready",
)


def _is_engineering_public_path(path: str) -> bool:
    normalized = normalize_path(path)
    if is_public_path(path):
        return True
    if normalized in _PUBLIC_EXACT:
        return True
    return normalized.endswith(_PUBLIC_SUFFIXES)


async def jwt_middleware(request, call_next):
    if _is_engineering_public_path(request.url.path):
        return await call_next(request)
    return await _base_jwt_middleware(request, call_next)
