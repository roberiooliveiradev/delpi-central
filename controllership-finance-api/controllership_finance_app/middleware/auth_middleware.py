from delpi_auth.jwt_validator import validate_token
from delpi_auth.middleware.fastapi_auth import (
    is_public_path,
    jwt_middleware as _base_jwt_middleware,
    normalize_path,
)
from delpi_auth.service_token import (
    request_has_valid_internal_service_token,
)
from delpi_mcp.auth import (
    McpTransportAuthPolicy,
    is_mcp_data_path,
    mcp_transport_auth,
)

from controllership_finance_app.interface.mcp.oauth_contract import (
    MCP_OAUTH_SCOPES,
    resolve_required_mcp_resource_audience,
)
from controllership_finance_app.interface.mcp.resource_metadata import (
    www_authenticate_challenge as _mcp_challenge,
)

__all__ = ["jwt_middleware"]


def _strip_root_path(request) -> str:
    path = request.url.path
    root_path = (request.scope.get("root_path") or "").rstrip("/")
    if root_path and path.startswith(root_path):
        return path[len(root_path):] or "/"
    return path


def _is_controllership_finance_public_path(path: str) -> bool:
    if path.startswith("/apps/controllership-finance-api/"):
        stripped = path[len("/apps/controllership-finance-api"):]
    else:
        stripped = path
    normalized = normalize_path(stripped)
    if is_public_path(path):
        return True
    if normalized.startswith("/public/"):
        return True
    if normalized in {"/ready", "/health"}:
        return True
    if normalized.endswith("/controllership-finance-api/ready") or normalized.endswith(
        "/controllership-finance-api/health"
    ):
        return True
    if normalized.startswith("/.well-known/oauth-protected-resource"):
        return True
    return False


# S3: transport AuthN MCP — JWT de usuário somente; service tokens são
# proibidos na superfície de dados. A AuthZ de negócio permanece nas
# tools/BFF (delpi_auth mantém o contexto canônico).
_MCP_TRANSPORT_POLICY = McpTransportAuthPolicy(
    resolve_resource_audience=resolve_required_mcp_resource_audience,
    required_scopes=MCP_OAUTH_SCOPES,
    challenge=_mcp_challenge,
    redecorate_base_401=True,
)


async def jwt_middleware(request, call_next):
    if _is_controllership_finance_public_path(request.url.path):
        return await call_next(request)
    normalized = normalize_path(_strip_root_path(request))
    if is_mcp_data_path(normalized):
        return await mcp_transport_auth(
            request,
            call_next,
            policy=_MCP_TRANSPORT_POLICY,
            token_validator=validate_token,
            service_token_gate=request_has_valid_internal_service_token,
            base_auth_middleware=_base_jwt_middleware,
        )
    return await _base_jwt_middleware(request, call_next)
