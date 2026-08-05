from delpi_auth.middleware.fastapi_auth import (
    is_public_path,
    jwt_middleware as _base_jwt_middleware,
    normalize_path,
)

__all__ = ["jwt_middleware"]


def _is_commercial_public_path(path: str) -> bool:
    normalized = normalize_path(path)
    if is_public_path(path):
        return True
    if normalized in {"/ready", "/health"}:
        return True
    return normalized.endswith("/commercial-api/ready") or normalized.endswith("/commercial-api/health")


async def jwt_middleware(request, call_next):
    if _is_commercial_public_path(request.url.path):
        return await call_next(request)
    return await _base_jwt_middleware(request, call_next)
