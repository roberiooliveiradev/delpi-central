# app/middleware/auth_middleware.py

from fastapi import Request

from delpi_auth.middleware.fastapi_auth import jwt_middleware as _base_jwt_middleware

__all__ = ["jwt_middleware"]

# Prefixos públicos (sem JWT) servidos pela api-delpi.
# Ex.: leitura pública da inspeção via QR (public-hub), protegida por token opaco.
_PUBLIC_PREFIXES = ("/public/quality-labels/",)

# root_path possíveis (o gateway costuma remover, mas mantemos robustez).
_ROOT_PREFIXES = ("/apps/api-delpi",)


def _strip_root(path: str) -> str:
    for root in _ROOT_PREFIXES:
        if path.startswith(root):
            return path[len(root):] or "/"
    return path


def _is_public_delpi_path(path: str) -> bool:
    normalized = _strip_root(path.split("?", 1)[0])
    return any(normalized.startswith(prefix) for prefix in _PUBLIC_PREFIXES)


async def jwt_middleware(request: Request, call_next):
    if _is_public_delpi_path(request.url.path):
        return await call_next(request)
    return await _base_jwt_middleware(request, call_next)
