"""DELPI-CHARACTER-AVATARS-001 — distribuição pública do avatar oficial VISTA."""

from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi.responses import FileResponse

from tv_app.interface.http.routes.characters_routes import (
    get_public_character_avatar,
)
from tv_app.middleware.auth_middleware import _is_public
from tv_app.persona.vista_profile import get_vista_profile

_EXPECTED_SHA256 = (
    "8d4879cc395361619d6b4c2623a04c029faaa41714283c76dec3e82ddc39d155"
)


def test_route_is_public_for_jwt_middleware() -> None:
    assert _is_public("/public/characters/vista/avatar/avatar-v2.jpg") is True


def test_approved_avatar_serves_official_bytes() -> None:
    response = get_public_character_avatar("vista", "avatar-v2.jpg")
    assert isinstance(response, FileResponse)
    assert response.media_type == "image/jpeg"
    assert response.headers["Cache-Control"] == "public, max-age=300"
    digest = hashlib.sha256(Path(response.path).read_bytes()).hexdigest()
    assert digest == _EXPECTED_SHA256


def test_wrong_character_id_fails_safe() -> None:
    response = get_public_character_avatar("teo", "avatar-v2.jpg")
    assert response.status_code == 404


def test_wrong_filename_fails_safe() -> None:
    for filename in ("avatar-v1.jpg", "avatar-v2.png", "../vista/avatar-v2.jpg"):
        response = get_public_character_avatar("vista", filename)
        assert response.status_code == 404


def test_profile_declares_approved_avatar() -> None:
    profile = get_vista_profile()
    assert profile.identity.character_id == "vista"
    assert profile.appearance.avatar_status == "OFFICIAL_AVATAR_APPROVED"
    assert profile.appearance.avatar_reference.endswith("avatar-v2.jpg")
