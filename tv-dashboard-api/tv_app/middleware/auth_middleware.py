from __future__ import annotations

from delpi_auth.middleware.fastapi_auth import jwt_middleware as _base_jwt_middleware
from fastapi import Request

from tv_app.middleware.media_access_token import resolve_media_query_authorization

PUBLIC_PREFIXES: tuple[str, ...] = ("/public/",)
PUBLIC_EXACT: frozenset[str] = frozenset({"/public", "/health"})


def _strip_root_path(request: Request) -> str:
    path = request.url.path
    root_path = (request.scope.get("root_path") or "").rstrip("/")
    if root_path and path.startswith(root_path):
        return path[len(root_path) :] or "/"
    return path


def _is_public(path: str) -> bool:
    if path in PUBLIC_EXACT:
        return True
    return any(path.startswith(prefix) for prefix in PUBLIC_PREFIXES)


def _inject_media_access_token_from_query(request: Request) -> None:
    auth = request.headers.get("Authorization") or request.headers.get("authorization")
    bearer = resolve_media_query_authorization(
        path=_strip_root_path(request),
        method=request.method,
        access_token=request.query_params.get("access_token"),
        existing_authorization=auth,
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
    if _is_public(_strip_root_path(request)):
        return await call_next(request)
    _inject_media_access_token_from_query(request)
    return await _base_jwt_middleware(request, call_next)
