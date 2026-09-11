from delpi_auth.middleware.fastapi_auth import jwt_middleware as _base_jwt_middleware
from fastapi import Request

PUBLIC_EXACT: frozenset[str] = frozenset({"/health"})
PUBLIC_PREFIXES: tuple[str, ...] = ("/device-ota/",)


def _strip_root_path(request: Request) -> str:
    path = request.url.path
    root_path = (request.scope.get("root_path") or "").rstrip("/")
    if root_path and path.startswith(root_path):
        return path[len(root_path) :] or "/"
    return path


def _normalize_path(path: str) -> str:
    normalized = (path or "/").strip() or "/"
    if len(normalized) > 1 and normalized.endswith("/"):
        return normalized.rstrip("/")
    return normalized


def _is_public(path: str) -> bool:
    normalized = _normalize_path(path)
    if normalized in PUBLIC_EXACT:
        return True
    # Token na query; o handler valida JWT + RBAC.
    if normalized.endswith("/v1/realtime/ws"):
        return True
    return any(normalized.startswith(prefix) for prefix in PUBLIC_PREFIXES)


async def jwt_middleware(request: Request, call_next):
    if _is_public(_strip_root_path(request)):
        return await call_next(request)
    return await _base_jwt_middleware(request, call_next)


class AuthMiddleware:
    """Compat wrapper — prefer ``app.middleware('http')(jwt_middleware)``."""

    async def __call__(self, request: Request, call_next):
        return await jwt_middleware(request, call_next)
