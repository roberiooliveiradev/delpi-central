from __future__ import annotations

import re

# GET /playlists/{uuid}/media/{uuid} — <img>/CSS/@font-face não enviam Authorization.
_ADMIN_MEDIA_PATH = re.compile(
    r"^/playlists/[0-9a-fA-F-]{36}/media/[0-9a-fA-F-]{36}/?$",
    re.IGNORECASE,
)
_ROOT_PREFIX = re.compile(r"^/apps/tv-dashboard-api(?=/|$)", re.IGNORECASE)


def normalize_tv_api_path(path: str, root_path: str = "") -> str:
    """Path da API sem prefixo de gateway (`/apps/tv-dashboard-api`)."""
    raw = (path or "/").split("?", 1)[0] or "/"
    roots = []
    for candidate in (root_path, "/apps/tv-dashboard-api"):
        trimmed = (candidate or "").strip().rstrip("/")
        if trimmed and trimmed not in roots:
            roots.append(trimmed)
    for root in roots:
        if raw == root:
            return "/"
        if raw.startswith(f"{root}/"):
            stripped = raw[len(root) :] or "/"
            return stripped if stripped.startswith("/") else f"/{stripped}"
    if _ROOT_PREFIX.match(raw):
        stripped = _ROOT_PREFIX.sub("", raw) or "/"
        return stripped if stripped.startswith("/") else f"/{stripped}"
    return raw if raw.startswith("/") else f"/{raw}"


def resolve_media_query_authorization(
    *,
    path: str,
    method: str,
    access_token: str | None,
    existing_authorization: str | None,
    root_path: str = "",
) -> str | None:
    """
    Se a rota for mídia admin e houver `access_token` na query, devolve
    `Bearer …` para injetar no request (mesmo contrato do WS admin).
    """
    if existing_authorization and existing_authorization.strip():
        return None
    if method.upper() not in {"GET", "HEAD"}:
        return None
    token = (access_token or "").strip()
    if not token:
        return None
    normalized = normalize_tv_api_path(path, root_path)
    if not _ADMIN_MEDIA_PATH.match(normalized):
        return None
    return f"Bearer {token}"
