"""DELPI-CHARACTER-AVATARS-001-R01 — distribuição pública do avatar oficial EVA
(publicação aprovada pelo PO; implementação ativa com controles preservados)."""

from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi.responses import FileResponse

from engineering_app.interface.http.routes.characters_routes import (
    _PUBLIC_DISTRIBUTION_ENABLED,
    get_public_character_avatar,
)
from engineering_app.middleware.auth_middleware import _is_engineering_public_path
from engineering_app.persona.eva_profile import get_eva_profile

_EXPECTED_SHA256 = (
    "18d9e05fc91388e236d3df6a8118634a604caeaf9dc0626bed4de240efc4e6fc"
)


def test_distribution_gate_is_open() -> None:
    assert _PUBLIC_DISTRIBUTION_ENABLED is True


def test_authorized_asset_path_is_public_exact_match() -> None:
    assert _is_engineering_public_path(
        "/public/characters/eva/avatar/avatar-v1.jpg"
    ) is True
    assert _is_engineering_public_path(
        "/apps/engineering-api/public/characters/eva/avatar/avatar-v1.jpg"
    ) is True


def test_no_generic_public_exemption() -> None:
    for path in (
        "/public/",
        "/public/characters/",
        "/public/characters/eva/avatar/avatar-v2.jpg",
        "/public/characters/clara/avatar/avatar-v1.jpg",
        "/public/anything-else",
        "/mcp",
    ):
        assert _is_engineering_public_path(path) is False, path


def test_approved_avatar_serves_official_bytes() -> None:
    response = get_public_character_avatar("eva", "avatar-v1.jpg")
    assert isinstance(response, FileResponse)
    assert response.media_type == "image/jpeg"
    assert response.headers["Cache-Control"] == "public, max-age=300"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    digest = hashlib.sha256(Path(response.path).read_bytes()).hexdigest()
    assert digest == _EXPECTED_SHA256


def test_wrong_character_id_fails_safe() -> None:
    response = get_public_character_avatar("vista", "avatar-v1.jpg")
    assert response.status_code == 404


def test_wrong_filename_fails_safe() -> None:
    for filename in ("avatar-v2.jpg", "avatar-v1.png", "../eva/avatar-v1.jpg"):
        response = get_public_character_avatar("eva", filename)
        assert response.status_code == 404


def test_profile_and_asset_are_the_approved_source() -> None:
    profile = get_eva_profile()
    assert profile.identity.character_id == "eva"
    assert profile.appearance.avatar_status == "OFFICIAL_AVATAR_APPROVED"
    api_root = Path(__file__).resolve().parents[1]
    assert (api_root / profile.appearance.avatar_reference).is_file()
