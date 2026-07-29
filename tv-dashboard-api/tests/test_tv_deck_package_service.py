"""Testes do pacote portátil `.delpi-tv-deck`."""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from tv_app.application.services.tv_deck_asset_collector import (
    collect_asset_ids,
    collect_data_bindings,
    rewrite_asset_ids,
)
from tv_app.application.services.tv_deck_binding_validator import TvDeckBindingValidator
from tv_app.application.services.tv_deck_package_service import (
    BINDINGS_INDEX_PATH,
    MANIFEST_FILENAME,
    MEDIA_INDEX_PATH,
    MEDIA_PREFIX,
    PACKAGE_FORMAT,
    PLAYLIST_PATH,
    SECTIONS_PATH,
    SLIDES_PATH,
    TvDeckPackageError,
    TvDeckPackageService,
    _PreviewStore,
    _is_safe_archive_path,
)


def test_collect_asset_ids_nested():
    ids = collect_asset_ids(
        {
            "masterConfig": {"logo": {"assetId": "a1"}, "background": {"assetId": "a2"}},
            "blocks": [{"type": "image", "assetId": "a3"}, {"customFonts": [{"assetId": "a4"}]}],
        }
    )
    assert ids == {"a1", "a2", "a3", "a4"}


def test_rewrite_asset_ids():
    out = rewrite_asset_ids(
        {"background": {"assetId": "old"}, "blocks": [{"assetId": "old"}]},
        {"old": "new"},
    )
    assert out["background"]["assetId"] == "new"
    assert out["blocks"][0]["assetId"] == "new"


def test_collect_data_bindings():
    items = collect_data_bindings(
        [
            {
                "sourceId": "s1",
                "nativeConfig": {
                    "blocks": [
                        {
                            "id": "b1",
                            "type": "data_kpi",
                            "dataBinding": {
                                "operationId": "get_overall_equipment_effectiveness_pct",
                                "params": {"branch": "01"},
                            },
                        }
                    ]
                },
            }
        ]
    )
    assert len(items) == 1
    assert items[0]["operationId"] == "get_overall_equipment_effectiveness_pct"
    assert items[0]["blockId"] == "b1"


def test_is_safe_archive_path_rejects_zip_slip():
    assert _is_safe_archive_path("manifest.json")
    assert _is_safe_archive_path("deck/playlist.json")
    assert _is_safe_archive_path("media/abc.png")
    assert not _is_safe_archive_path("../etc/passwd")
    assert not _is_safe_archive_path("/abs/path")
    assert not _is_safe_archive_path("media/../secret")


def test_binding_validator_unknown_route_is_warning():
    catalog = MagicMock()
    catalog.get_route.return_value = None
    validator = TvDeckBindingValidator(catalog=catalog)
    report = validator.validate_one({"operationId": "does_not_exist", "blockType": "data_kpi"})
    assert report["status"] == "warning"
    assert TvDeckBindingValidator.has_blocking_errors([report], binding_policy="lenient") is False
    assert TvDeckBindingValidator.has_blocking_errors([report], binding_policy="strict") is True


def test_binding_validator_ok_route():
    catalog = MagicMock()
    catalog.get_route.return_value = {
        "operationId": "get_overall_equipment_effectiveness_pct",
        "httpMethod": "GET",
        "allowedDisplayModes": ["auto", "kpi"],
        "paramSchema": {},
        "tvConstraints": {"maxRows": 90},
    }
    validator = TvDeckBindingValidator(catalog=catalog)
    report = validator.validate_one(
        {
            "operationId": "get_overall_equipment_effectiveness_pct",
            "blockType": "data_kpi",
            "params": {},
            "displayMode": "kpi",
        }
    )
    assert report["status"] == "ok"


def _build_playlist_fixture(asset_id: str) -> dict[str, Any]:
    return {
        "id": str(uuid4()),
        "name": "Deck Demo",
        "description": "desc",
        "viewportProfile": "1080p",
        "transitionStyle": "fade",
        "defaultDurationSec": 30,
        "globalRefreshSec": 300,
        "dataDefaults": {"branch": "01"},
        "masterConfig": {"enabled": True, "logo": {"assetId": asset_id}},
        "publicToken": "tok",
        "isActive": True,
        "viewCount": 0,
        "ownerUserId": "user-a",
        "createdBy": "user-a",
        "revision": 1,
    }


def test_export_preview_apply_roundtrip(tmp_path: Path):
    asset_id = str(uuid4())
    playlist = _build_playlist_fixture(asset_id)
    playlist_id = playlist["id"]
    section_id = str(uuid4())
    slide_id = str(uuid4())

    sections = [
        {
            "id": section_id,
            "name": "Principal",
            "sortOrder": 0,
            "isCollapsed": False,
            "isActive": True,
            "isMain": True,
            "defaultDurationSec": None,
            "transitionStyle": None,
            "masterConfig": {},
        }
    ]
    slides = [
        {
            "id": slide_id,
            "sectionId": section_id,
            "sortOrder": 0,
            "slideType": "native",
            "durationSec": 20,
            "title": "Comunicado",
            "nativeScreenKey": "custom_message",
            "nativeConfig": {
                "version": 4,
                "blocks": [
                    {
                        "id": "img1",
                        "type": "image",
                        "assetId": asset_id,
                        "frame": {"x": 0, "y": 0, "w": 20, "h": 20},
                    },
                    {
                        "id": "kpi1",
                        "type": "data_kpi",
                        "dataBinding": {
                            "operationId": "op_missing_in_catalog",
                            "params": {},
                            "displayMode": "kpi",
                        },
                        "frame": {"x": 30, "y": 0, "w": 20, "h": 20},
                    },
                ],
                "background": {"type": "color", "value": "#fff"},
            },
            "externalUrl": None,
            "externalSandbox": None,
            "isActive": True,
            "transitionStyle": None,
        }
    ]
    media_row = {
        "id": asset_id,
        "playlistId": playlist_id,
        "storedName": f"{asset_id.replace('-', '')}.png",
        "originalName": "logo.png",
        "mimeType": "image/png",
        "mediaKind": "image",
        "fileSizeBytes": 4,
        "createdBy": "user-a",
        "createdAt": None,
    }

    storage = MagicMock()
    storage.read.return_value = b"\x89PNG"
    storage.save.return_value = ("newstored.png", "image/png", "image")

    playlist_repo = MagicMock()
    playlist_repo.get_by_id.return_value = playlist
    playlist_repo.list_slides.return_value = slides
    playlist_repo.list_sections.return_value = sections

    created_playlist = {
        **playlist,
        "id": str(uuid4()),
        "name": "Deck Demo",
        "ownerUserId": "user-b",
        "isActive": False,
        "publicToken": "new-token",
    }
    playlist_repo.create.return_value = created_playlist
    playlist_repo.update.return_value = created_playlist
    playlist_repo.import_sections_from_deck.return_value = {section_id: str(uuid4())}
    playlist_repo.import_slides_from_deck.return_value = []
    playlist_repo.set_active.return_value = created_playlist

    media_repo = MagicMock()
    media_repo.list_for_playlist.return_value = [media_row]
    media_repo.create.return_value = {
        "id": str(uuid4()),
        "storedName": "newstored.png",
        "mimeType": "image/png",
        "mediaKind": "image",
    }

    catalog = MagicMock()
    catalog.get_route.return_value = None
    validator = TvDeckBindingValidator(catalog=catalog)
    preview_store = _PreviewStore(ttl_seconds=60)

    service = TvDeckPackageService(
        playlist_repo=playlist_repo,
        media_repo=media_repo,
        media_storage=storage,
        binding_validator=validator,
        max_bytes=10 * 1024 * 1024,
        preview_store=preview_store,
    )

    # Export
    payload, filename = service.export_package(uuid4(), exported_by="user-a")
    assert filename.endswith(".delpi-tv-deck")
    assert payload[:2] == b"PK"

    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        names = set(zf.namelist())
        assert MANIFEST_FILENAME in names
        assert PLAYLIST_PATH in names
        assert SECTIONS_PATH in names
        assert SLIDES_PATH in names
        assert MEDIA_INDEX_PATH in names
        assert BINDINGS_INDEX_PATH in names
        assert any(n.startswith(MEDIA_PREFIX) for n in names)
        manifest = json.loads(zf.read(MANIFEST_FILENAME))
        assert manifest["format"] == PACKAGE_FORMAT
        assert manifest["stats"]["mediaCount"] == 1

    # Preview (lenient warnings for missing binding)
    preview = service.preview_import(payload)
    assert preview["valid"] is True
    assert preview.get("importToken")
    assert any("op_missing_in_catalog" in w for w in preview.get("warnings") or [])

    # Strict apply must fail while token still valid — use fresh preview
    preview2 = service.preview_import(payload)
    with pytest.raises(TvDeckPackageError, match="strict|bindings"):
        service.apply_import(
            import_token=preview2["importToken"],
            created_by="user-b",
            binding_policy="strict",
        )

    # Lenient apply (cross-account owner user-b)
    preview3 = service.preview_import(payload)
    result = service.apply_import(
        import_token=preview3["importToken"],
        created_by="user-b",
        binding_policy="lenient",
        name_override="Importada B",
    )
    assert result["accessRole"] == "owner"
    playlist_repo.create.assert_called()
    media_repo.create.assert_called()
    storage.save.assert_called()
    # asset remap applied in update masterConfig
    update_kwargs = playlist_repo.update.call_args.kwargs
    assert update_kwargs["master_config"]["logo"]["assetId"] != asset_id


def test_preview_rejects_bad_checksum():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        playlist = json.dumps({"name": "X", "masterConfig": {}}).encode()
        sections = b"[]"
        slides = b"[]"
        media = b"[]"
        zf.writestr(PLAYLIST_PATH, playlist)
        zf.writestr(SECTIONS_PATH, sections)
        zf.writestr(SLIDES_PATH, slides)
        zf.writestr(MEDIA_INDEX_PATH, media)
        manifest = {
            "format": PACKAGE_FORMAT,
            "schemaVersion": "1.0",
            "entries": {
                PLAYLIST_PATH: {"sha256": "deadbeef", "size_bytes": len(playlist)},
                SECTIONS_PATH: {
                    "sha256": __import__("hashlib").sha256(sections).hexdigest(),
                    "size_bytes": len(sections),
                },
                SLIDES_PATH: {
                    "sha256": __import__("hashlib").sha256(slides).hexdigest(),
                    "size_bytes": len(slides),
                },
                MEDIA_INDEX_PATH: {
                    "sha256": __import__("hashlib").sha256(media).hexdigest(),
                    "size_bytes": len(media),
                },
            },
            "stats": {},
        }
        zf.writestr(MANIFEST_FILENAME, json.dumps(manifest).encode())
    service = TvDeckPackageService(max_bytes=1024 * 1024, preview_store=_PreviewStore())
    preview = service.preview_import(buffer.getvalue())
    assert preview["valid"] is False
    assert any("Checksum" in e for e in preview["errors"])


def test_preview_rejects_zip_slip():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("../evil.txt", b"x")
        zf.writestr(
            MANIFEST_FILENAME,
            json.dumps({"format": PACKAGE_FORMAT, "schemaVersion": "1.0"}).encode(),
        )
    service = TvDeckPackageService(max_bytes=1024 * 1024, preview_store=_PreviewStore())
    preview = service.preview_import(buffer.getvalue())
    assert preview["valid"] is False
    assert any("inválido" in e.lower() or "Caminho" in e for e in preview["errors"])


def test_export_fails_when_media_missing_on_disk():
    asset_id = str(uuid4())
    playlist = _build_playlist_fixture(asset_id)
    playlist_repo = MagicMock()
    playlist_repo.get_by_id.return_value = playlist
    playlist_repo.list_slides.return_value = [
        {
            "id": str(uuid4()),
            "sectionId": None,
            "sortOrder": 0,
            "slideType": "native",
            "title": "T",
            "nativeScreenKey": "custom_message",
            "nativeConfig": {"blocks": [{"id": "1", "type": "image", "assetId": asset_id}]},
            "isActive": True,
        }
    ]
    playlist_repo.list_sections.return_value = []
    media_repo = MagicMock()
    media_repo.list_for_playlist.return_value = [
        {
            "id": asset_id,
            "storedName": "gone.png",
            "mimeType": "image/png",
            "mediaKind": "image",
            "originalName": "gone.png",
        }
    ]
    storage = MagicMock()
    storage.read.return_value = None
    service = TvDeckPackageService(
        playlist_repo=playlist_repo,
        media_repo=media_repo,
        media_storage=storage,
        max_bytes=1024 * 1024,
        preview_store=_PreviewStore(),
    )
    with pytest.raises(TvDeckPackageError, match="ausentes"):
        service.export_package(uuid4())
