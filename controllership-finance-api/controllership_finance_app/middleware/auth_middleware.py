from delpi_auth.middleware.fastapi_auth import (
    is_public_path,
    jwt_middleware as _base_jwt_middleware,
    normalize_path,
)

__all__ = ["jwt_middleware"]


def _is_controllership_finance_public_path(path: str) -> bool:
    normalized = normalize_path(path)
    if is_public_path(path):
        return True
    if normalized in {"/ready", "/health"}:
        return True
    if normalized.endswith("/controllership-finance-api/ready") or normalized.endswith(
        "/controllership-finance-api/health"
    ):
        return True
    return False


async def jwt_middleware(request, call_next):
    if _is_controllership_finance_public_path(request.url.path):
        return await call_next(request)
    return await _base_jwt_middleware(request, call_next)
