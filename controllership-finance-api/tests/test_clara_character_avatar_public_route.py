"""DELPI-CHARACTER-AVATARS-001 — distribuição pública do avatar oficial CLARA."""

from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi.responses import FileResponse

from controllership_finance_app.interface.http.routes.characters_routes import (
    get_public_character_avatar,
)
from controllership_finance_app.middleware.auth_middleware import (
    _is_controllership_finance_public_path,
)
from controllership_finance_app.persona.clara_profile import get_clara_profile

_EXPECTED_SHA256 = (
    "967e79b8086673f34b52e574330e7d94669728cfe60269005e754c3fc49f140f"
)


def test_route_is_public_for_jwt_middleware() -> None:
    assert _is_controllership_finance_public_path(
        "/public/characters/clara/avatar/avatar-v1.jpg"
    ) is True


def test_approved_avatar_serves_official_bytes() -> None:
    response = get_public_character_avatar("clara", "avatar-v1.jpg")
    assert isinstance(response, FileResponse)
    assert response.media_type == "image/jpeg"
    assert response.headers["Cache-Control"] == "public, max-age=300"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    digest = hashlib.sha256(Path(response.path).read_bytes()).hexdigest()
    assert digest == _EXPECTED_SHA256


def test_wrong_character_id_fails_safe() -> None:
    response = get_public_character_avatar("davi", "avatar-v1.jpg")
    assert response.status_code == 404


def test_wrong_filename_fails_safe() -> None:
    for filename in ("avatar-v2.jpg", "avatar-v1.png", "../clara/avatar-v1.jpg"):
        response = get_public_character_avatar("clara", filename)
        assert response.status_code == 404


def test_profile_declares_approved_avatar() -> None:
    profile = get_clara_profile()
    assert profile.identity.character_id == "clara"
    assert profile.appearance.avatar_status == "OFFICIAL_AVATAR_APPROVED"
    assert profile.appearance.avatar_reference.endswith("avatar-v1.jpg")
