"""AuthN do Portal de TI — middleware canônico `delpi_auth` com allowlist estrita.

Público: liveness, contrato (docs/OpenAPI) e prefixo `/collector/v1/` (AuthN
S2S é aplicada na própria rota de ingestão — sem JWT de usuário). Nenhum dado
de inventário humano é servido sem JWT + permissão efetiva do Core.
"""

from delpi_auth.middleware.fastapi_auth import (
    jwt_middleware as _base_jwt_middleware,
    normalize_path,
)

__all__ = ["jwt_middleware", "is_it_portal_public_path"]

_ROOT_PATH = "/apps/it-portal-api"
_PUBLIC_PATHS = frozenset({"/health", "/openapi.json", "/docs", "/redoc"})
_COLLECTOR_PREFIX = "/collector/v1"


def is_it_portal_public_path(path: str) -> bool:
    normalized = normalize_path(path)
    if normalized.startswith(_ROOT_PATH + "/") or normalized == _ROOT_PATH:
        normalized = normalized[len(_ROOT_PATH) :] or "/"
    if normalized in _PUBLIC_PATHS:
        return True
    return normalized == _COLLECTOR_PREFIX or normalized.startswith(_COLLECTOR_PREFIX + "/")


async def jwt_middleware(request, call_next):
    return await _base_jwt_middleware(
        request, call_next, public_path_checker=is_it_portal_public_path
    )
