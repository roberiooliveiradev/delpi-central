from delpi_auth.middleware.fastapi_auth import jwt_middleware as _base_jwt_middleware
from fastapi import Request

PUBLIC_EXACT = frozenset({"/health", "/auth/glpi/callback"})


def _strip_root_path(request: Request) -> str:
    path = request.url.path
    root_path = (request.scope.get("root_path") or "").rstrip("/")
    if root_path and path.startswith(root_path):
        return path[len(root_path) :] or "/"
    return path


async def jwt_middleware(request: Request, call_next):
    if _strip_root_path(request) in PUBLIC_EXACT:
        return await call_next(request)
    return await _base_jwt_middleware(request, call_next)
