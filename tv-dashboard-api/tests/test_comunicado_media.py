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


def test_media_storage_accepts_woff2_font():
    with tempfile.TemporaryDirectory() as tmp:
        storage = MediaStorageService(base_dir=tmp)
        stored, mime, kind = storage.save(content=b"wOF2", mime_type="font/woff2")
        assert stored.endswith(".woff2")
        assert kind == "font"
        assert mime == "font/woff2"


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


def test_comunicado_enrichment_blank_slide_keeps_rich_empty_blocks():
    """Slide em branco (blocks []) não vira legado com Título / fundo escuro."""
    service = ComunicadoEnrichmentService(media_repo=MagicMock())
    data = service.enrich(
        {"version": 4, "headline": "", "blocks": [], "background": {"type": "color", "value": "#ffffff"}},
        api_root_path="/apps/tv-dashboard-api",
        playlist_id=str(uuid4()),
    )
    assert data["blocks"] == []
    assert data["headline"] == ""
    assert data["background"] == {"type": "color", "value": "#ffffff"}


def test_comunicado_enrichment_default_background_is_white():
    service = ComunicadoEnrichmentService(media_repo=MagicMock())
    data = service.enrich(
        {"blocks": [{"id": "1", "type": "text", "content": "x", "frame": {"x": 0, "y": 0, "w": 10, "h": 10}}]},
        api_root_path="/apps/tv-dashboard-api",
        playlist_id=str(uuid4()),
    )
    assert data["background"] == {"type": "color", "value": "#ffffff"}


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


def test_comunicado_enrichment_resolves_custom_font_url():
    asset_id = str(uuid4())
    playlist_id = str(uuid4())
    repo = MagicMock()
    repo.get_for_playlist.return_value = {"id": asset_id, "mediaKind": "font"}
    service = ComunicadoEnrichmentService(media_repo=repo)
    data = service.enrich(
        {
            "blocks": [],
            "customFonts": [{"assetId": asset_id, "familyName": "Minha Fonte"}],
        },
        api_root_path="/apps/tv-dashboard-api",
        playlist_id=playlist_id,
    )
    assert data["customFonts"] == [
        {
            "assetId": asset_id,
            "familyName": "Minha Fonte",
            "url": f"/apps/tv-dashboard-api/playlists/{playlist_id}/media/{asset_id}",
        }
    ]


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


def test_enrich_preserves_data_source_and_chart_view_for_preview():
    """Prévia/link público: não stripar binding nem chartType (tela branca)."""
    data_enrichment = MagicMock()
    data_enrichment.enrich_blocks.side_effect = lambda blocks, **_kw: blocks
    service = ComunicadoEnrichmentService(
        media_repo=MagicMock(),
        data_enrichment=data_enrichment,
    )
    playlist_id = str(uuid4())
    data = service.enrich(
        {
            "blocks": [
                {
                    "id": "src-1",
                    "type": "data_source",
                    "frame": {"x": 0, "y": 0, "w": 10, "h": 10},
                    "dataBinding": {
                        "operationId": "get_on_time_delivery_pct",
                        "params": {"periodDays": 30},
                        "displayMode": "auto",
                    },
                },
                {
                    "id": "chart-1",
                    "type": "chart_view",
                    "dataSourceId": "src-1",
                    "chartType": "line",
                    "chartOptions": {"showDataTable": True},
                    "chartParts": {"title": {"visible": True}},
                    "frame": {"x": 5, "y": 5, "w": 90, "h": 80},
                    "animations": {"entrance": "fade"},
                },
            ]
        },
        api_root_path="/apps/tv-dashboard-api",
        playlist_id=playlist_id,
        public_token="share-token",
    )
    assert data["version"] == 4
    passed = data_enrichment.enrich_blocks.call_args.args[0]
    assert passed[0]["type"] == "data_source"
    assert passed[0]["dataBinding"]["operationId"] == "get_on_time_delivery_pct"
    assert passed[1]["type"] == "chart_view"
    assert passed[1]["dataSourceId"] == "src-1"
    assert passed[1]["chartType"] == "line"
    assert passed[1]["chartOptions"]["showDataTable"] is True
    assert passed[1]["chartParts"]["title"]["visible"] is True
    assert passed[1]["animations"]["entrance"] == "fade"
    data_enrichment.enrich_blocks.assert_called_once()
    assert data_enrichment.enrich_blocks.call_args.kwargs.get("authorization") is None


def test_enrich_preserves_input_param_key_for_preview():
    """Prévia/apresentação: não stripar input.paramKey (senão «Parâmetro indisponível»)."""
    data_enrichment = MagicMock()
    data_enrichment.enrich_blocks.side_effect = lambda blocks, **_kw: blocks
    service = ComunicadoEnrichmentService(
        media_repo=MagicMock(),
        data_enrichment=data_enrichment,
    )
    data = service.enrich(
        {
            "blocks": [
                {
                    "id": "input-1",
                    "type": "input",
                    "frame": {"x": 5, "y": 5, "w": 30, "h": 12},
                    "input": {
                        "paramKey": "branch",
                        "label": "Filial",
                        "defaultValue": "01",
                        "targetScope": "slide",
                    },
                    "inputParts": {"control": {"visible": True}},
                },
            ]
        },
        api_root_path="/apps/tv-dashboard-api",
        playlist_id=str(uuid4()),
    )
    passed = data_enrichment.enrich_blocks.call_args.args[0]
    assert passed[0]["type"] == "input"
    assert passed[0]["input"]["paramKey"] == "branch"
    assert passed[0]["input"]["label"] == "Filial"
    assert passed[0]["inputParts"]["control"]["visible"] is True
    assert data["blocks"][0]["input"]["paramKey"] == "branch"
