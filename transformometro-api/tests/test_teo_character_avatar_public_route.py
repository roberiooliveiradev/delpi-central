"""DELPI-CHARACTER-AVATARS-001 — distribuição pública do avatar oficial TÉO."""

from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi.responses import FileResponse

from tm_app.interface.http.routes.characters_routes import (
    get_public_character_avatar,
)
from tm_app.middleware.auth_middleware import _is_public
from tm_app.persona.teo_profile import get_teo_profile

_EXPECTED_SHA256 = (
    "51f5bab4603a818d6f857603b8b3d15e1472c875c5221619a8b91d8e0cad8c8b"
)


def test_route_is_public_for_jwt_middleware() -> None:
    assert _is_public("/public/characters/teo/avatar/avatar-v2.png") is True


def test_approved_avatar_v2_serves_official_bytes() -> None:
    response = get_public_character_avatar("teo", "avatar-v2.png")
    assert isinstance(response, FileResponse)
    assert response.media_type == "image/png"
    assert response.headers["Cache-Control"] == "public, max-age=300"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    digest = hashlib.sha256(Path(response.path).read_bytes()).hexdigest()
    assert digest == _EXPECTED_SHA256


def test_superseded_v1_is_not_published() -> None:
    response = get_public_character_avatar("teo", "avatar-v1.png")
    assert response.status_code == 404


def test_wrong_character_id_fails_safe() -> None:
    response = get_public_character_avatar("vista", "avatar-v2.png")
    assert response.status_code == 404


def test_path_traversal_fails_safe() -> None:
    response = get_public_character_avatar("teo", "../teo/avatar-v2.png")
    assert response.status_code == 404


def test_profile_declares_approved_avatar_v2() -> None:
    profile = get_teo_profile()
    assert profile.identity.character_id == "teo"
    assert profile.appearance.avatar_status == "OFFICIAL_AVATAR_APPROVED"
    assert profile.appearance.avatar_reference.endswith("avatar-v2.png")
