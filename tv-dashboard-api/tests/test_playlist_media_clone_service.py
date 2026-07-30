"""Clonagem de mídia ao duplicar programação (imagem + vídeo)."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

from tv_app.application.services.playlist_media_clone_service import PlaylistMediaCloneService
from tv_app.application.services.tv_deck_asset_collector import collect_asset_ids, rewrite_asset_ids


def test_collect_asset_ids_includes_video_blocks():
    ids = collect_asset_ids(
        {
            "blocks": [
                {"type": "image", "assetId": "img-1"},
                {"type": "video", "assetId": "vid-1"},
            ]
        }
    )
    assert ids == {"img-1", "vid-1"}


def test_rewrite_asset_ids_maps_video_and_image():
    out = rewrite_asset_ids(
        {
            "blocks": [
                {"type": "video", "assetId": "old-v"},
                {"type": "image", "assetId": "old-i"},
            ]
        },
        {"old-v": "new-v", "old-i": "new-i"},
    )
    assert out["blocks"][0]["assetId"] == "new-v"
    assert out["blocks"][1]["assetId"] == "new-i"


def test_clone_media_and_remap_copies_video_and_rewrites_slide():
    source_id = uuid4()
    target_id = uuid4()
    video_source = str(uuid4())
    video_target = str(uuid4())
    slide_id = str(uuid4())

    media = MagicMock()
    media.list_for_playlist.return_value = [
        {
            "id": video_source,
            "storedName": "aaa.mp4",
            "originalName": "clip.mp4",
            "mimeType": "video/mp4",
            "mediaKind": "video",
        }
    ]
    media.create.return_value = {"id": video_target}

    storage = MagicMock()
    storage.read.return_value = b"fake-video-bytes"
    storage.save.return_value = ("bbb.mp4", "video/mp4", "video")

    playlists = MagicMock()
    playlists.get_by_id.return_value = {
        "id": str(target_id),
        "masterConfig": {},
    }
    playlists.list_sections.return_value = []
    playlists.list_slides.return_value = [
        {
            "id": slide_id,
            "nativeConfig": {
                "version": 2,
                "blocks": [{"type": "video", "assetId": video_source}],
            },
        }
    ]

    service = PlaylistMediaCloneService(media=media, storage=storage, playlists=playlists)
    id_map = service.clone_media_and_remap(
        source_playlist_id=source_id,
        target_playlist_id=target_id,
        created_by="user-1",
    )

    assert id_map == {video_source: video_target}
    media.create.assert_called_once()
    playlists.bulk_replace_asset_configs.assert_called_once()
    kwargs = playlists.bulk_replace_asset_configs.call_args.kwargs
    assert kwargs["slide_native_configs"][slide_id]["blocks"][0]["assetId"] == video_target
