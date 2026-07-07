import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from tv_app.application.services.comunicado_enrichment_service import ComunicadoEnrichmentService
from tv_app.application.services.media_storage_service import MediaStorageService, MediaValidationError


def test_media_storage_accepts_png():
    with tempfile.TemporaryDirectory() as tmp:
        storage = MediaStorageService(base_dir=tmp)
        stored, mime, kind = storage.save(content=b"\x89PNG", mime_type="image/png")
        assert kind == "image"
        assert mime == "image/png"
        assert storage.read(stored) == b"\x89PNG"


def test_media_storage_rejects_unknown_type():
    with tempfile.TemporaryDirectory() as tmp:
        storage = MediaStorageService(base_dir=tmp)
        with pytest.raises(MediaValidationError):
            storage.save(content=b"data", mime_type="application/pdf")


def test_comunicado_enrichment_legacy_headline():
    service = ComunicadoEnrichmentService(media_repo=MagicMock())
    data = service.enrich(
        {"headline": "Olá", "subtitle": "Equipe"},
        api_root_path="/apps/tv-dashboard-api",
        playlist_id=str(uuid4()),
    )
    assert data["headline"] == "Olá"
    assert data["subtitle"] == "Equipe"
    assert "blocks" not in data


def test_comunicado_enrichment_resolves_media_url():
    asset_id = str(uuid4())
    playlist_id = str(uuid4())
    repo = MagicMock()
    repo.get_for_playlist.return_value = {"id": asset_id}
    service = ComunicadoEnrichmentService(media_repo=repo)
    data = service.enrich(
        {
            "blocks": [
                {
                    "id": "b1",
                    "type": "image",
                    "assetId": asset_id,
                    "frame": {"x": 0, "y": 0, "w": 50, "h": 50},
                }
            ]
        },
        api_root_path="/apps/tv-dashboard-api",
        playlist_id=playlist_id,
    )
    assert data["version"] >= 2
    assert data["blocks"][0]["url"] == f"/apps/tv-dashboard-api/playlists/{playlist_id}/media/{asset_id}"


def test_custom_message_with_blocks():
    from tv_app.application.services.native_screen_data_service import NativeScreenDataService

    service = NativeScreenDataService(comunicado=ComunicadoEnrichmentService(media_repo=MagicMock()))
    data = service.resolve(
        screen_key="custom_message",
        config={
            "blocks": [{"id": "1", "type": "heading", "content": "Evento", "frame": {"x": 5, "y": 5, "w": 90, "h": 20}}],
        },
        playlist_id=str(uuid4()),
    )
    assert data["version"] >= 2
    assert data["blocks"][0]["content"] == "Evento"
