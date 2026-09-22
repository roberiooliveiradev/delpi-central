"""Notify playlist-scoped and user-library WebSocket rooms."""

from __future__ import annotations

import time
from typing import Any, Iterable
from uuid import UUID

from tv_app.application.services.presentation_realtime_hub import (
    presentation_realtime_hub,
    user_library_room_id,
)
from tv_app.application.services.presentation_sync_service import build_presentation_content_revision

LIBRARY_REASONS = frozenset(
    {
        "created",
        "updated",
        "deleted",
        "renamed",
        "activated",
        "deactivated",
        "duplicated",
        "shared",
        "imported",
    }
)


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


def notify_playlist_library_changed(
    *,
    user_ids: Iterable[str],
    reason: str,
    playlist_id: str | None = None,
) -> None:
    """Fan-out to PlaylistsPage library rooms (user-scoped)."""
    reason_norm = str(reason or "").strip().lower()
    if reason_norm not in LIBRARY_REASONS:
        reason_norm = "updated"
    seen: set[str] = set()
    payload_base: dict[str, Any] = {
        "type": "playlist_library_updated",
        "reason": reason_norm,
        "updatedAt": int(time.time() * 1000),
    }
    if playlist_id:
        payload_base["playlistId"] = str(playlist_id)
    for raw in user_ids:
        uid = str(raw or "").strip()
        if not uid or uid in seen:
            continue
        seen.add(uid)
        room = user_library_room_id(uid)
        if not room:
            continue
        presentation_realtime_hub.schedule_broadcast(room, dict(payload_base))


def resolve_library_recipient_user_ids(
    playlist: dict[str, Any] | None,
    *,
    extra_user_ids: Iterable[str] | None = None,
    shares: list[dict[str, Any]] | None = None,
) -> list[str]:
    """Owner + share targets (+ extras). Deduped."""
    out: list[str] = []
    seen: set[str] = set()

    def _add(value: Any) -> None:
        uid = str(value or "").strip()
        if uid and uid not in seen:
            seen.add(uid)
            out.append(uid)

    if isinstance(playlist, dict):
        _add(playlist.get("ownerUserId") or playlist.get("createdBy"))
    for share in shares or []:
        if isinstance(share, dict):
            _add(share.get("targetUserId"))
    for extra in extra_user_ids or []:
        _add(extra)
    return out
