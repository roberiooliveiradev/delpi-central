from delpi_auth.jwt_validator import validate_token
from delpi_auth.middleware.fastapi_auth import (
    is_public_path,
    jwt_middleware as _base_jwt_middleware,
    normalize_path,
)
from delpi_auth.service_token import request_has_valid_internal_service_token
from delpi_mcp.auth import (
    McpTransportAuthPolicy,
    is_mcp_data_path,
    mcp_transport_auth,
)

from commercial_app.interface.mcp.constants import MCP_GATEWAY_ROOT
from commercial_app.interface.mcp.oauth_contract import (
    MCP_OAUTH_SCOPES,
    build_www_authenticate_challenge,
    resolve_required_mcp_resource_audience,
)
from commercial_app.interface.mcp.resource_metadata import (
    MCP_RESOURCE_CONFIG,
)

__all__ = ["jwt_middleware"]

# Variantes prefixadas das rotas técnicas públicas — sob
# uvicorn --root-path, request.url.path inclui /apps/commercial-api.
_PUBLIC_PATHS = frozenset(
    {
        "/ready",
        "/health",
        "/apps/commercial-api/ready",
        "/apps/commercial-api/health",
    }
)

# RFC 9728 metadata é discovery pública — derivada das rotas efetivamente
# registradas (MCP_RESOURCE_CONFIG.metadata_paths) e de sua variante
# prefixada sob root_path/gateway. Comparação exata após normalize_path.
_PUBLIC_OAUTH_METADATA_PATHS = frozenset(
    set(MCP_RESOURCE_CONFIG.metadata_paths)
    | {
        f"{MCP_GATEWAY_ROOT.rstrip('/')}{path}"
        for path in MCP_RESOURCE_CONFIG.metadata_paths
    }
)

# DELPI-CHARACTER-AVATARS-001-R01: avatar oficial CAIO — distribuição
# pública aprovada pelo PO. Asset único, comparação exata (a ficha do
# personagem valida status/referência; o path nunca é resolvido do request).
_PUBLIC_CHARACTER_AVATAR_PATHS = frozenset(
    {
        "/public/characters/caio/avatar/avatar-v1.jpg",
        "/apps/commercial-api/public/characters/caio/avatar/avatar-v1.jpg",
    }
)


def _is_commercial_public_path(path: str) -> bool:
    normalized = normalize_path(path)
    if is_public_path(path):
        return True
    if normalized in _PUBLIC_PATHS:
        return True
    if normalized in _PUBLIC_OAUTH_METADATA_PATHS:
        return True
    if normalized in _PUBLIC_CHARACTER_AVATAR_PATHS:
        return True
    # Token vai na query; o handler valida JWT + RBAC (como o Transformômetro).
    if normalized.endswith("/commercial/realtime/ws"):
        return True
    return False


def _strip_root_path(request) -> str:
    path = request.url.path
    root_path = (request.scope.get("root_path") or "").rstrip("/")
    if root_path and path.startswith(root_path):
        return path[len(root_path) :] or "/"
    return path


# MCP transport AuthN policy — user JWT only; service tokens proibidos
# na superfície MCP (delegação humana preservada). AuthZ de negócio
# permanece application-owned (delpi_auth → Core /me).
_MCP_TRANSPORT_POLICY = McpTransportAuthPolicy(
    resolve_resource_audience=resolve_required_mcp_resource_audience,
    required_scopes=MCP_OAUTH_SCOPES,
    challenge=build_www_authenticate_challenge,
    redecorate_base_401=True,
)


async def _commercial_base_auth(request, call_next):
    return await _base_jwt_middleware(
        request, call_next, public_path_checker=_is_commercial_public_path
    )


async def jwt_middleware(request, call_next):
    """AuthN oficial delpi_auth com allowlist estrita do Comercial.

    Caminhos MCP (/mcp) exigem o transporte OAuth dedicado (Bearer JWT +
    audience exata + scopes); demais rotas seguem a auth canônica com a
    allowlist pública local.
    """
    normalized = normalize_path(
        _strip_root_path(request).split("?", 1)[0]
    )
    if is_mcp_data_path(normalized):
        return await mcp_transport_auth(
            request,
            call_next,
            policy=_MCP_TRANSPORT_POLICY,
            token_validator=validate_token,
            service_token_gate=request_has_valid_internal_service_token,
            base_auth_middleware=_commercial_base_auth,
        )
    return await _commercial_base_auth(request, call_next)
