"""Playlist lifecycle commands — delete and history restore.

Keeps concrete persistence adapters out of the gpt_actions facade
(application-layer boundary). Both commands delegate to the canonical
repositories and emit the domain notifications the REST routes emit.
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from tv_app.infrastructure.persistence.repositories.playlist_repository import (
    PlaylistRepository,
)
from tv_app.infrastructure.persistence.repositories.playlist_history_repository import (
    PlaylistHistoryNotFoundError,
    PlaylistHistoryRepository,
)
from tv_app.application.errors.playlist_persistence import (
    PlaylistRevisionConflictError,
)
from tv_app.application.services.presentation_change_notifier import (
    notify_presentation_changed,
)

__all__ = [
    "PlaylistHistoryNotFoundError",
    "PlaylistRevisionConflictError",
    "delete_playlist",
    "get_playlist_state",
    "restore_playlist_history",
]


def get_playlist_state(playlist_id: UUID) -> dict[str, Any] | None:
    return PlaylistRepository().get_by_id(playlist_id)


def delete_playlist(playlist_id: UUID) -> None:
    PlaylistRepository().delete(playlist_id)
    notify_presentation_changed(
        playlist_id=str(playlist_id), reason="playlist_deleted"
    )


def restore_playlist_history(
    playlist_id: UUID,
    history_id: UUID,
    *,
    expected_revision: int | None,
    actor_user_id: str,
    reason: str = "vista_history_restored",
) -> dict[str, Any]:
    revision = PlaylistHistoryRepository().restore(
        playlist_id,
        history_id,
        expected_revision=expected_revision,
        actor_user_id=actor_user_id,
        reason=reason,
    )
    playlist = PlaylistRepository().get_by_id(playlist_id) or {}
    notify_presentation_changed(
        playlist_id=str(playlist_id),
        reason="history_restored",
        revision=str(revision),
    )
    return {"revision": revision, "playlist": playlist}
