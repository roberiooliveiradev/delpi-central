from __future__ import annotations

from delpi_auth.middleware.fastapi_auth import jwt_middleware as _base_jwt_middleware
from fastapi import Request

from tv_app.interface.http.gpt_actions_response import (
    correlation_id_from_request,
    gpt_fail,
)
from tv_app.middleware.media_access_token import (
    normalize_tv_api_path,
    resolve_media_query_authorization,
)

PUBLIC_PREFIXES: tuple[str, ...] = ("/public/",)
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


async def jwt_middleware(request: Request, call_next):
    # Path bruto do ASGI (com ou sem root_path) — `_is_public` normaliza.
    if _is_public(request.url.path) or _is_public(_strip_root_path(request)):
        return await call_next(request)
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
