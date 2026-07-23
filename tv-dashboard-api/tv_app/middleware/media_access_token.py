from __future__ import annotations

import re

# GET /playlists/{uuid}/media/{uuid} — <img>/CSS/@font-face não enviam Authorization.
_ADMIN_MEDIA_PATH = re.compile(
    r"^/playlists/[0-9a-fA-F-]{36}/media/[0-9a-fA-F-]{36}/?$",
    re.IGNORECASE,
)


def resolve_media_query_authorization(
    *,
    path: str,
    method: str,
    access_token: str | None,
    existing_authorization: str | None,
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
    if not _ADMIN_MEDIA_PATH.match(path):
        return None
    return f"Bearer {token}"
