from __future__ import annotations

from delpi_auth.middleware.fastapi_auth import jwt_middleware as _base_jwt_middleware
from fastapi import Request

from tv_app.middleware.media_access_token import (
    normalize_tv_api_path,
    resolve_media_query_authorization,
)

PUBLIC_PREFIXES: tuple[str, ...] = ("/public/",)
PUBLIC_EXACT: frozenset[str] = frozenset({"/public", "/health"})


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


async def jwt_middleware(request: Request, call_next):
    # Path bruto do ASGI (com ou sem root_path) — `_is_public` normaliza.
    if _is_public(request.url.path) or _is_public(_strip_root_path(request)):
        return await call_next(request)
    _inject_media_access_token_from_query(request)
    return await _base_jwt_middleware(request, call_next)
