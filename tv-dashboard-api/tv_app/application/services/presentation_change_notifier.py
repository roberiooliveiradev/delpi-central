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
    slide_id: str | None = None,
    playlist_revision: int | None = None,
) -> None:
    # Save/estrutura mudou — inválida TTL de dados para present/preview não
    # servirem IDD/KPI stale (viewer puro = mesmos números após flush).
    from tv_app.application.services.comunicado_data_enrichment_service import (
        reset_comunicado_data_block_cache,
    )

    reset_comunicado_data_block_cache()

    payload: dict[str, Any] = {
        "type": "presentation_updated",
        "reason": reason,
        "playlistId": str(playlist_id),
    }
    if slide_id:
        payload["slideId"] = str(slide_id)
    if playlist_revision is not None:
        payload["playlistRevision"] = int(playlist_revision)
    resolved_revision = revision
    if not resolved_revision:
        try:
            resolved_revision = build_presentation_content_revision(UUID(str(playlist_id)))
        except (ValueError, TypeError):
            resolved_revision = None
    if resolved_revision:
        payload["revision"] = resolved_revision
    presentation_realtime_hub.schedule_broadcast(str(playlist_id), payload)
