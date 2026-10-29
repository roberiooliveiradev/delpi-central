"""DELPI-CHARACTER-AVATARS-001 — distribuição pública do avatar oficial DAVI."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from fastapi.responses import FileResponse

from app.interface.http.route_contract_registry import ROUTE_CONTRACTS
from app.interface.http.routes.characters.characters_public_router import (
    get_public_character_avatar,
)
from app.middleware.auth_middleware import _is_public_delpi_path
from app.persona.davi_profile import get_davi_profile

_API_ROOT = Path(__file__).resolve().parents[1]
_EXPECTED_SHA256 = (
    "94494e3a0c5ccc4672f4cb765e7e23785d48001f2a66514a86f4d356f281b98e"
)


def test_operation_id_registered_in_route_contracts() -> None:
    assert "get_public_character_avatar" in ROUTE_CONTRACTS


def test_route_is_inside_public_prefix() -> None:
    assert _is_public_delpi_path(
        "/public/characters/davi/avatar/avatar-v1.png"
    ) is True


def test_approved_avatar_serves_official_bytes() -> None:
    response = get_public_character_avatar("davi", "avatar-v1.png")
    assert isinstance(response, FileResponse)
    assert response.media_type == "image/png"
    assert response.headers["Cache-Control"] == "public, max-age=300"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    digest = hashlib.sha256(Path(response.path).read_bytes()).hexdigest()
    assert digest == _EXPECTED_SHA256


def test_wrong_character_id_fails_safe() -> None:
    response = get_public_character_avatar("clara", "avatar-v1.png")
    assert response.status_code == 404
    assert json.loads(bytes(response.body))["error"]["code"] == "NOT_FOUND"


def test_wrong_filename_fails_safe() -> None:
    for filename in ("avatar-v2.png", "avatar-v1.jpg", "..%2Fsecret.png"):
        response = get_public_character_avatar("davi", filename)
        assert response.status_code == 404


def test_path_traversal_cannot_escape() -> None:
    response = get_public_character_avatar("davi", "../davi/avatar-v1.png")
    assert response.status_code == 404


def test_unapproved_status_blocks_publication() -> None:
    profile = get_davi_profile()
    assert profile.appearance.avatar_status == "OFFICIAL_AVATAR_APPROVED"
    assert (_API_ROOT / profile.appearance.avatar_reference).is_file()
