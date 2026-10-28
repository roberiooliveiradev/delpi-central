from delpi_auth.middleware.fastapi_auth import (
    jwt_middleware as _base_jwt_middleware,
    normalize_path,
)

__all__ = ["jwt_middleware"]

# Allowlist estrita do contrato da Engenharia — comparação exata após
# normalize_path (sem sufixo, sem prefixo arbitrário). /openapi.json e
# /docs|/redoc preservam a política canônica da lib para paths exatos.
_PUBLIC_PATHS = frozenset(
    {
        "/health",
        "/ready",
        "/apps/engineering-api/health",
        "/apps/engineering-api/ready",
        "/docs",
        "/redoc",
        "/openapi.json",
    }
)


def _is_engineering_public_path(path: str) -> bool:
    return normalize_path(path) in _PUBLIC_PATHS


async def jwt_middleware(request, call_next):
    """AuthN oficial delpi_auth com allowlist estrita da Engenharia.

    O predicado é declarado via ``public_path_checker`` — a política
    pública da lib (mais ampla: sufixo docs/openapi de qualquer prefixo,
    /apps/<outro-svc>/health) não se aplica aqui, e o request path nunca
    é mutado.
    """
    return await _base_jwt_middleware(
        request, call_next, public_path_checker=_is_engineering_public_path
    )
