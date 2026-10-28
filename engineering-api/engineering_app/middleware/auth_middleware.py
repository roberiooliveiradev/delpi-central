from delpi_auth.jwt_validator import validate_token
from delpi_auth.middleware.fastapi_auth import (
    jwt_middleware as _base_jwt_middleware,
    normalize_path,
)
from delpi_auth.service_token import request_has_valid_internal_service_token
from delpi_mcp.auth import (
    McpTransportAuthPolicy,
    is_mcp_data_path,
    mcp_transport_auth,
)

from engineering_app.interface.mcp.constants import MCP_GATEWAY_ROOT
from engineering_app.interface.mcp.oauth_contract import (
    MCP_OAUTH_SCOPES,
    build_www_authenticate_challenge,
    resolve_required_mcp_resource_audience,
)
from engineering_app.interface.mcp.resource_metadata import (
    MCP_RESOURCE_CONFIG,
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
        # Variantes prefixadas: sob uvicorn --root-path, request.url.path
        # inclui o root_path — as formas prefixadas das rotas técnicas
        # públicas precisam estar na allowlist exata.
        "/apps/engineering-api/docs",
        "/apps/engineering-api/redoc",
        "/apps/engineering-api/openapi.json",
    }
)


# RFC 9728 metadata é discovery pública — derivada das rotas efetivamente
# registradas (MCP_RESOURCE_CONFIG.metadata_paths) e de sua variante
# prefixada: sob root_path/gateway o url.path chega como
# /apps/engineering-api/…. Comparação exata após normalize_path — nunca
# substring (EVA.MCP.V1.R1).
_PUBLIC_OAUTH_METADATA_PATHS = frozenset(
    set(MCP_RESOURCE_CONFIG.metadata_paths)
    | {
        f"{MCP_GATEWAY_ROOT}{path}"
        for path in MCP_RESOURCE_CONFIG.metadata_paths
    }
)


def _is_engineering_public_path(path: str) -> bool:
    normalized = normalize_path(path)
    return (
        normalized in _PUBLIC_PATHS
        or normalized in _PUBLIC_OAUTH_METADATA_PATHS
    )


def _strip_root_path(request) -> str:
    path = request.url.path
    root_path = (request.scope.get("root_path") or "").rstrip("/")
    if root_path and path.startswith(root_path):
        return path[len(root_path) :] or "/"
    return path


# S3: MCP transport AuthN policy — user JWT only; service tokens
# proibidos na superfície MCP (delegação humana F2a.R1 preservada).
# AuthZ de negócio permanece application-owned (delpi_auth → Core /me).
_MCP_TRANSPORT_POLICY = McpTransportAuthPolicy(
    resolve_resource_audience=resolve_required_mcp_resource_audience,
    required_scopes=MCP_OAUTH_SCOPES,
    challenge=build_www_authenticate_challenge,
    redecorate_base_401=True,
)


async def _engineering_base_auth(request, call_next):
    return await _base_jwt_middleware(
        request, call_next, public_path_checker=_is_engineering_public_path
    )


async def jwt_middleware(request, call_next):
    """AuthN oficial delpi_auth com allowlist estrita da Engenharia.

    O predicado é declarado via ``public_path_checker`` — a política
    pública da lib (mais ampla: sufixo docs/openapi de qualquer prefixo,
    /apps/<outro-svc>/health) não se aplica aqui, e o request path nunca
    é mutado. Caminhos MCP (/mcp) exigem o transporte OAuth dedicado.
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
            base_auth_middleware=_engineering_base_auth,
        )
    return await _engineering_base_auth(request, call_next)
