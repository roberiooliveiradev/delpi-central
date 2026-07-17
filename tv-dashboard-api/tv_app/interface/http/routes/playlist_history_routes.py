from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

from tv_app.application.services.playlist_access_service import PlaylistAccessService
from tv_app.application.services.presentation_change_notifier import notify_presentation_changed
from tv_app.core.responses import fail, ok
from tv_app.infrastructure.persistence.repositories.playlist_history_repository import (
    PlaylistHistoryNotFoundError,
    PlaylistHistoryRepository,
    PlaylistRevisionConflictError,
)
from tv_app.infrastructure.persistence.repositories.playlist_repository import PlaylistRepository
from tv_app.interface.http.playlist_access_http import is_access_error, require_playlist_access

router = APIRouter(prefix="/playlists/{playlist_id}/history", tags=["Playlist history"])
_history_repo = PlaylistHistoryRepository()
_playlist_repo = PlaylistRepository()
_access = PlaylistAccessService()


class RestorePlaylistBody(BaseModel):
    expectedRevision: int = Field(ge=0)
    reason: str | None = Field(default=None, min_length=1, max_length=500)


def _actor_or_error(user):
    actor = _access.actor_id(user)
    if not actor:
        return None, fail("Usuário não identificado.", 401)
    return actor, None


@router.get("")
def list_playlist_history(
    request: Request,
    playlist_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100, alias="pageSize"),
):
    guarded = require_playlist_access(request, playlist_id, need="read")
    if is_access_error(guarded):
        return guarded
    return ok(_history_repo.list_history(playlist_id, page=page, page_size=page_size))


@router.get("/{history_id}")
def get_playlist_history(request: Request, playlist_id: UUID, history_id: UUID):
    guarded = require_playlist_access(request, playlist_id, need="read")
    if is_access_error(guarded):
        return guarded
    try:
        item = _history_repo.get_history(playlist_id, history_id)
    except PlaylistHistoryNotFoundError:
        return fail("Versão do histórico não encontrada.", 404)
    return ok(item)


@router.post("/{history_id}/restore")
def restore_playlist_history(
    request: Request,
    playlist_id: UUID,
    history_id: UUID,
    body: RestorePlaylistBody,
):
    guarded = require_playlist_access(request, playlist_id, need="edit")
    if is_access_error(guarded):
        return guarded
    user, _ = guarded
    actor, actor_error = _actor_or_error(user)
    if actor_error:
        return actor_error
    try:
        revision = _history_repo.restore(
            playlist_id,
            history_id,
            expected_revision=body.expectedRevision,
            actor_user_id=actor,
            reason=(body.reason or "history_restored").strip(),
        )
    except PlaylistRevisionConflictError as exc:
        return fail(
            "A programação foi alterada por outro usuário.",
            409,
            data={"currentRevision": exc.current_revision},
        )
    except PlaylistHistoryNotFoundError:
        return fail("Versão do histórico não encontrada.", 404)

    playlist = _playlist_repo.get_by_id(playlist_id) or {}
    playlist["slides"] = _playlist_repo.list_slides(playlist_id)
    notify_presentation_changed(
        playlist_id=str(playlist_id),
        reason="history_restored",
        revision=str(revision),
    )
    return ok(
        {
            "playlist": playlist,
            "selectedSlideId": None,
            "revision": revision,
            "snapshotId": str(history_id),
            "restoredFromSnapshotId": str(history_id),
        },
        message="Versão restaurada.",
    )
