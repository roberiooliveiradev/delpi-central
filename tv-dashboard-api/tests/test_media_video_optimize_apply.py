from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

from tv_app.application.services.media_video_optimize_apply import (
    apply_video_optimize_after_create,
    reoptimize_video_asset,
)
from tv_app.application.services.media_video_optimize_service import VideoOptimizeResult


def test_apply_video_optimize_skips_non_video():
    asset = {"id": str(uuid4()), "mediaKind": "image", "storedName": "a.png"}
    out = apply_video_optimize_after_create(
        asset=asset,
        media_repo=MagicMock(),
        storage=MagicMock(),
    )
    assert out is asset


def test_apply_video_optimize_updates_repo():
    asset_id = uuid4()
    asset = {
        "id": str(asset_id),
        "mediaKind": "video",
        "storedName": "clip.mp4",
        "mimeType": "video/mp4",
    }
    media_repo = MagicMock()
    storage = MagicMock()
    storage.resolve_path.return_value = MagicMock()
    storage.base_dir = MagicMock()
    media_repo.update_video_optimize.return_value = {**asset, "hasPoster": True}

    optimizer = MagicMock()
    optimizer.optimize_stored_video.return_value = VideoOptimizeResult(
        poster_stored_name="p.poster.jpg",
        duration_ms=1000,
        width_px=1280,
        height_px=720,
        file_size_bytes=99,
        optimized=True,
    )

    out = apply_video_optimize_after_create(
        asset=asset,
        media_repo=media_repo,
        storage=storage,
        optimizer=optimizer,
    )
    media_repo.update_video_optimize.assert_called_once()
    assert out["hasPoster"] is True


def test_reoptimize_returns_none_when_missing():
    media_repo = MagicMock()
    media_repo.get_for_playlist.return_value = None
    assert (
        reoptimize_video_asset(
            playlist_id=uuid4(),
            asset_id=uuid4(),
            media_repo=media_repo,
            storage=MagicMock(),
        )
        is None
    )


def test_build_media_poster_url():
    from tv_app.application.services.comunicado_enrichment_service import (
        ComunicadoEnrichmentService,
    )

    assert ComunicadoEnrichmentService.build_media_poster_url(
        api_root_path="/apps/tv-dashboard-api",
        playlist_id="p1",
        asset_id="a1",
        public_token="tok",
    ) == "/apps/tv-dashboard-api/public/present/tok/media/a1/poster"
