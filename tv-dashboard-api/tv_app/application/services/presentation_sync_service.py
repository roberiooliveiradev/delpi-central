from __future__ import annotations

from uuid import UUID

from tv_app.infrastructure.persistence.repositories.playlist_repository import PlaylistRepository


def build_presentation_content_revision(playlist_id: UUID, *, repo: PlaylistRepository | None = None) -> str:
    repository = repo or PlaylistRepository()
    return repository.get_presentation_content_revision(playlist_id)
