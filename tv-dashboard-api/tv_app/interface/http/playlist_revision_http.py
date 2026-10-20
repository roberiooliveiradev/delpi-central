"""Concorrência otimista por ``playlists.revision`` (If-Match).

O copiloto envia a revisão lida no plano; o MFE pode omitir (compatível).
Conflito → 409 com ``currentRevision``.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import Request
from fastapi.responses import JSONResponse

from tv_app.application.errors.playlist_persistence import (
    PlaylistRevisionConflictError,
)
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


logger = logging.getLogger(__name__)


def log_playlist_write_rejected(
    *,
    playlist_id: Any = None,
    slide_id: Any = None,
    request_id: Any = None,
    actor: Any = None,
    client_id: Any = None,
    operation: Any = None,
    expected_revision: Any = None,
    current_revision: Any = None,
    result: str = "revision_conflict",
) -> None:
    """Log estruturado canônico de rejeição de escrita (CAS/409).

    Metadados de correlação apenas — nunca tokens, cookies ou conteúdo.
    """
    logger.warning(
        "playlist_write_rejected playlist_id=%s slide_id=%s request_id=%s "
        "actor=%s client_id=%s operation=%s expected_revision=%s "
        "current_revision=%s result=%s",
        playlist_id,
        slide_id,
        request_id,
        actor,
        client_id,
        operation,
        expected_revision,
        current_revision,
        result,
    )


def playlist_revision_conflict_response(
    exc: PlaylistRevisionConflictError,
    *,
    expected: int | None,
    log_context: dict[str, Any] | None = None,
) -> JSONResponse:
    """409 canônico para conflito de CAS atômico vindo do repositório."""
    ctx = log_context or {}
    log_playlist_write_rejected(
        playlist_id=ctx.get("playlistId"),
        slide_id=ctx.get("slideId"),
        request_id=ctx.get("requestId"),
        actor=ctx.get("actor"),
        client_id=ctx.get("clientId"),
        operation=ctx.get("operation"),
        expected_revision=int(expected) if expected is not None else None,
        current_revision=int(exc.current_revision),
    )
    return fail(
        "A programação foi alterada por outro editor. Recarregue e tente de novo.",
        409,
        data={
            "currentRevision": int(exc.current_revision),
            "expectedRevision": int(expected) if expected is not None else None,
        },
    )


def revision_response_headers(revision: int) -> dict[str, str]:
    return {"X-Playlist-Revision": str(int(revision))}


def with_revision(data: Any, revision: int) -> Any:
    """Anexa playlistRevision ao payload de sucesso quando for dict."""
    if isinstance(data, dict):
        out = dict(data)
        out["playlistRevision"] = int(revision)
        return out
    return data
