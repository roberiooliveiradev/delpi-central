from delpi_auth.middleware.fastapi_auth import (
    is_public_path,
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
    path = request.url.path
    if _is_engineering_public_path(path):
        return await call_next(request)

    if is_public_path(path):
        # A lib compartilhada aceita uma política pública mais ampla que o
        # contrato da Engenharia (sufixo /docs|/redoc|/openapi.json de
        # qualquer prefixo, /apps/<outro-svc>/health, */api-delpi/health).
        # Esses paths não podem dispensar JWT aqui: mascaramos o path só
        # durante a avaliação do middleware base — que executa todo o fluxo
        # de autenticação oficial — e restauramos antes do call_next para
        # que o roteamento veja o path real.
        real_path = request.scope["path"]
        request.scope["path"] = "/"
        request.__dict__.pop("_url", None)  # Starlette cacheia url por request

        async def _restoring_call_next(req):
            req.scope["path"] = real_path
            req.__dict__.pop("_url", None)
            return await call_next(req)

        try:
            return await _base_jwt_middleware(request, _restoring_call_next)
        finally:
            request.scope["path"] = real_path
            request.__dict__.pop("_url", None)

    return await _base_jwt_middleware(request, call_next)
