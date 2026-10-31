"""Query-side accessor for playlist media assets.

Keeps the concrete persistence adapter out of the gpt_actions facade
(application-layer boundary): semantic reads call this service, which
delegates to the canonical media repository.
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from tv_app.infrastructure.persistence.repositories.media_repository import (
    MediaRepository,
)


def list_playlist_media(
    playlist_id: UUID,
    *,
    media_kind: str | None = None,
) -> list[dict[str, Any]]:
    return MediaRepository().list_for_playlist(
        playlist_id, media_kind=media_kind
    )
