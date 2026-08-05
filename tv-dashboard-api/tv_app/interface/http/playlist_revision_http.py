"""Concorrência otimista por ``playlists.revision`` (If-Match).

O copiloto envia a revisão lida no plano; o MFE pode omitir (compatível).
Conflito → 409 com ``currentRevision``.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import Request
from fastapi.responses import JSONResponse

from tv_app.core.responses import fail
from tv_app.infrastructure.persistence.repositories.playlist_repository import (
    PlaylistRepository,
)


def parse_if_match_revision(request: Request) -> int | None:
    raw = (request.headers.get("If-Match") or "").strip()
    if not raw:
        return None
    # Aceita: 12 | "12" | W/"12"
    cleaned = raw.strip().removeprefix("W/").strip().strip('"').strip("'")
    if not cleaned:
        return None
    try:
        return int(cleaned)
    except ValueError:
        return None


def assert_playlist_revision_or_conflict(
    repo: PlaylistRepository,
    playlist_id: UUID,
    *,
    expected: int | None,
) -> JSONResponse | int:
    """Retorna revisão atual (int) ou Response 409."""
    current = repo.get_revision(playlist_id)
    if expected is None:
        return current
    if current != int(expected):
        return fail(
            "A programação foi alterada por outro editor. Recarregue e tente de novo.",
            409,
            data={"currentRevision": current, "expectedRevision": int(expected)},
        )
    return current


def revision_response_headers(revision: int) -> dict[str, str]:
    return {"X-Playlist-Revision": str(int(revision))}


def with_revision(data: Any, revision: int) -> Any:
    """Anexa playlistRevision ao payload de sucesso quando for dict."""
    if isinstance(data, dict):
        out = dict(data)
        out["playlistRevision"] = int(revision)
        return out
    return data
