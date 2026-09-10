from delpi_auth.middleware.fastapi_auth import (
    is_public_path,
    jwt_middleware as _base_jwt_middleware,
    normalize_path,
)

__all__ = ["jwt_middleware"]


def _is_requests_public_path(path: str) -> bool:
    normalized = normalize_path(path)
    if is_public_path(path):
        return True
    if normalized in {"/ready", "/health"}:
        return True
    if normalized.endswith("/requests-api/ready") or normalized.endswith(
        "/requests-api/health"
    ):
        return True
    # Token na query; o handler valida JWT + RBAC.
    if normalized.endswith("/v1/realtime/ws"):
        return True
    return False


async def jwt_middleware(request, call_next):
    if _is_requests_public_path(request.url.path):
        return await call_next(request)
    return await _base_jwt_middleware(request, call_next)
