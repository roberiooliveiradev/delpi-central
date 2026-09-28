from __future__ import annotations

from delpi_auth.jwt_validator import validate_token
from delpi_auth.middleware.fastapi_auth import jwt_middleware as _base_jwt_middleware
from delpi_auth.service_token import request_has_valid_internal_service_token
from fastapi import Request
from fastapi.responses import JSONResponse

from tv_app.interface.http.gpt_actions_response import (
    correlation_id_from_request,
    gpt_fail,
)
from tv_app.interface.mcp.oauth_contract import (
    build_www_authenticate_challenge,
    mcp_audience_satisfied,
    mcp_required_scopes_satisfied,
)
from tv_app.middleware.media_access_token import (
    normalize_tv_api_path,
    resolve_media_query_authorization,
)

PUBLIC_PREFIXES: tuple[str, ...] = (
    "/public/",
    # RFC 9728 OAuth Protected Resource Metadata — public discovery for MCP.
    "/.well-known/oauth-protected-resource",
)
PUBLIC_EXACT: frozenset[str] = frozenset(
    {
        "/public",
        "/health",
        # Custom GPT import — exact schema path only (fail-closed; never prefix /gpt-actions/).
        "/gpt-actions/v1/openapi.json",
    }
)
_GPT_ACTIONS_PREFIX = "/gpt-actions/v1/"
_GPT_ACTIONS_OPENAPI = "/gpt-actions/v1/openapi.json"


def _strip_root_path(request: Request) -> str:
    return normalize_tv_api_path(
        request.url.path,
        str(request.scope.get("root_path") or ""),
    )


def _is_public(path: str) -> bool:
    normalized = normalize_tv_api_path(path)
    if normalized in PUBLIC_EXACT:
        return True
    if any(normalized.startswith(prefix) for prefix in PUBLIC_PREFIXES):
        return True
    # Defesa: URL absoluta do gateway ainda contendo o prefixo público.
    return "/public/present/" in (path or "")


def _inject_media_access_token_from_query(request: Request) -> None:
    auth = request.headers.get("Authorization") or request.headers.get("authorization")
    bearer = resolve_media_query_authorization(
        path=request.url.path,
        method=request.method,
        access_token=request.query_params.get("access_token"),
        existing_authorization=auth,
        root_path=str(request.scope.get("root_path") or ""),
    )
    if not bearer:
        return
    headers = [
        (name, value)
        for name, value in request.scope.get("headers", [])
        if name.lower() != b"authorization"
    ]
    headers.append((b"authorization", bearer.encode("latin-1")))
    request.scope["headers"] = headers


def _normalized_api_path(request: Request) -> str:
    return normalize_tv_api_path(
        request.url.path,
        str(request.scope.get("root_path") or ""),
    )


def _is_gpt_actions_protected_path(path: str) -> bool:
    """GPT Actions surface that must speak ``GptErrorEnvelope`` on auth failure."""
    normalized = normalize_tv_api_path(path)
    if not normalized.startswith(_GPT_ACTIONS_PREFIX):
        return False
    return normalized != _GPT_ACTIONS_OPENAPI


_MCP_PREFIX = "/mcp"


def _is_mcp_data_path(path: str) -> bool:
    """MCP JSON-RPC transport (mounted app). Metadata well-known stays public."""
    normalized = normalize_tv_api_path(path)
    return normalized == _MCP_PREFIX or normalized.startswith(_MCP_PREFIX + "/")


def _oauth_json_401() -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={"detail": "Unauthorized"},
        headers={"WWW-Authenticate": build_www_authenticate_challenge()},
    )


async def _mcp_oauth_transport(request: Request, call_next):
    """MCP transport authn: OAuth Bearer + resource audience + generic scopes.

    Internal service tokens are forbidden on /mcp — the transport requires a
    user Bearer token whose `aud` contains the exact MCP resource URL and
    whose `scope` contains the generic MCP scopes. Business AuthZ remains
    application-owned downstream.
    """
    if request_has_valid_internal_service_token(request):
        return _oauth_json_401()
    auth = request.headers.get("Authorization") or request.headers.get("authorization")
    if not auth or not auth.startswith("Bearer "):
        return _oauth_json_401()
    token = auth.split(" ", 1)[1].strip()
    if not token:
        return _oauth_json_401()
    try:
        payload = validate_token(token)
    except Exception:
        return _oauth_json_401()
    if not mcp_audience_satisfied(payload):
        return _oauth_json_401()
    if not mcp_required_scopes_satisfied(payload):
        return _oauth_json_401()
    return await _base_jwt_middleware(request, call_next)


async def jwt_middleware(request: Request, call_next):
    # Path bruto do ASGI (com ou sem root_path) — `_is_public` normaliza.
    if _is_public(request.url.path) or _is_public(_strip_root_path(request)):
        return await call_next(request)
    # MCP transport: OAuth Bearer + resource audience + scopes + challenge.
    if _is_mcp_data_path(request.url.path) or _is_mcp_data_path(_strip_root_path(request)):
        return await _mcp_oauth_transport(request, call_next)
    _inject_media_access_token_from_query(request)
    response = await _base_jwt_middleware(request, call_next)
    # Representation only: shared middleware still owns AuthN decision.
    if getattr(response, "status_code", None) != 401:
        return response
    path = _normalized_api_path(request)
    if not _is_gpt_actions_protected_path(path):
        return response
    headers: dict[str, str] = {}
    www = response.headers.get("www-authenticate") or response.headers.get(
        "WWW-Authenticate"
    )
    if www:
        headers["WWW-Authenticate"] = www
    return gpt_fail(
        code="AUTHENTICATION_REQUIRED",
        message="Autenticação necessária.",
        status_code=401,
        correlation_id=correlation_id_from_request(request),
        headers=headers or None,
    )
