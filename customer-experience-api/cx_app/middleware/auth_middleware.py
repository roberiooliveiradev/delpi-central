"""Auth middleware do Customer Experience.

As rotas sob `/public/` são a superfície pública (página de agradecimento por token
opaco) e não exigem JWT. Todo o restante delega ao middleware JWT compartilhado do
`delpi_auth` (mesma validação Keycloak + RBAC usada pelas demais APIs do portal).
"""

from __future__ import annotations

from fastapi import Request

from delpi_auth.middleware.fastapi_auth import jwt_middleware as _base_jwt_middleware

__all__ = ["jwt_middleware"]

PUBLIC_PREFIXES: tuple[str, ...] = ("/public/",)
PUBLIC_EXACT: frozenset[str] = frozenset({"/public"})


def _strip_root_path(request: Request) -> str:
    """Path sem o root_path do ASGI (o proxy expõe /apps/<svc>/... como prefixo)."""
    path = request.url.path.split("?", 1)[0]
    root = request.scope.get("root_path") or ""
    if root and path.startswith(root):
        path = path[len(root):] or "/"
    return path


def _is_public(path: str) -> bool:
    if path in PUBLIC_EXACT:
        return True
    return any(path.startswith(prefix) for prefix in PUBLIC_PREFIXES)


async def jwt_middleware(request: Request, call_next):
    if _is_public(_strip_root_path(request)):
        return await call_next(request)
    return await _base_jwt_middleware(request, call_next)
