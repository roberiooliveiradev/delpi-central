from __future__ import annotations

from typing import Any
from uuid import UUID

from tv_app.application.services.presentation_realtime_hub import presentation_realtime_hub
from tv_app.application.services.presentation_sync_service import build_presentation_content_revision


def notify_presentation_changed(
    *,
    playlist_id: str,
    reason: str,
    revision: str | None = None,
) -> None:
    payload: dict[str, Any] = {
        "type": "presentation_updated",
        "reason": reason,
        "playlistId": str(playlist_id),
    }
    resolved_revision = revision
    if not resolved_revision:
        try:
            resolved_revision = build_presentation_content_revision(UUID(str(playlist_id)))
        except (ValueError, TypeError):
            resolved_revision = None
    if resolved_revision:
        payload["revision"] = resolved_revision
    presentation_realtime_hub.schedule_broadcast(str(playlist_id), payload)
