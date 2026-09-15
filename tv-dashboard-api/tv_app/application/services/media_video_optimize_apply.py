"""Helpers compartilhados para otimizar vídeo após persistir o asset."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from tv_app.application.services.media_storage_service import MediaStorageService
from tv_app.application.services.media_video_optimize_service import MediaVideoOptimizeService
from tv_app.infrastructure.persistence.repositories.media_repository import MediaRepository

logger = logging.getLogger(__name__)


def apply_video_optimize_after_create(
    *,
    asset: dict[str, Any],
    media_repo: MediaRepository,
    storage: MediaStorageService,
    optimizer: MediaVideoOptimizeService | None = None,
) -> dict[str, Any]:
    """Best-effort: faststart + poster. Nunca invalida o upload."""
    if str(asset.get("mediaKind") or "") != "video":
        return asset
    stored = str(asset.get("storedName") or "").strip()
    if not stored:
        return asset
    path = storage.resolve_path(stored)
    if path is None:
        return asset

    service = optimizer or MediaVideoOptimizeService()
    try:
        result = service.optimize_stored_video(
            media_path=path,
            mime_type=str(asset.get("mimeType") or ""),
            base_dir=storage.base_dir,
        )
    except Exception:
        logger.exception("video optimize crashed for asset %s", asset.get("id"))
        return asset

    if not result.optimized and not result.poster_stored_name:
        return asset

    try:
        asset_id = UUID(str(asset["id"]))
    except (KeyError, ValueError, TypeError):
        return asset

    updated = media_repo.update_video_optimize(
        asset_id=asset_id,
        poster_stored_name=result.poster_stored_name,
        duration_ms=result.duration_ms,
        width_px=result.width_px,
        height_px=result.height_px,
        file_size_bytes=result.file_size_bytes,
        mark_optimized=True,
    )
    return updated or asset


def reoptimize_video_asset(
    *,
    playlist_id: UUID,
    asset_id: UUID,
    media_repo: MediaRepository,
    storage: MediaStorageService,
    optimizer: MediaVideoOptimizeService | None = None,
) -> dict[str, Any] | None:
    asset = media_repo.get_for_playlist(playlist_id, asset_id)
    if not asset or str(asset.get("mediaKind") or "") != "video":
        return None
    # Remove poster antigo antes de regenerar.
    old_poster = asset.get("posterStoredName")
    if isinstance(old_poster, str) and old_poster.strip():
        storage.delete(old_poster.strip())
    return apply_video_optimize_after_create(
        asset=asset,
        media_repo=media_repo,
        storage=storage,
        optimizer=optimizer,
    )
