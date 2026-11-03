"""Vínculo de ator autenticado para rotas que auditam ator via ContextVar.

Executa como middleware http (contexto da requisição), **depois** do
`jwt_middleware` que popula `request.state.user`. Dependências FastAPI com
`yield` não podem propagar ContextVar de forma segura — enter/exit rodam em
contextos distintos e o `reset()` quebrava com
`ValueError: Token was created in a different Context` (incidente 03/11/2026).
"""

from __future__ import annotations

from delpi_auth.middleware.fastapi_auth import normalize_path

from commercial_app.core.auth_actor import bind_request_actor

_ACTOR_BOUND_PREFIX = "/seller-portfolios"


def _strip_root_path(request) -> str:
    path = request.url.path
    root_path = (request.scope.get("root_path") or "").rstrip("/")
    if root_path and path.startswith(root_path):
        return path[len(root_path):] or "/"
    return path


async def actor_binding_middleware(request, call_next):
    normalized = normalize_path(_strip_root_path(request).split("?", 1)[0])
    if normalized == _ACTOR_BOUND_PREFIX or normalized.startswith(
        f"{_ACTOR_BOUND_PREFIX}/"
    ):
        bind_request_actor(request)
    return await call_next(request)
