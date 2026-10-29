"""DELPI-CHARACTER-AVATARS-001 — EVA: implementação preparada, publicação
bloqueada até ratificação do PO (D05 / DECISION_REQUIRED)."""

from __future__ import annotations

from pathlib import Path

from engineering_app.interface.http.routes.characters_routes import (
    _PUBLIC_DISTRIBUTION_ENABLED,
    get_public_character_avatar,
)
from engineering_app.middleware.auth_middleware import _is_engineering_public_path
from engineering_app.persona.eva_profile import get_eva_profile


def test_distribution_gate_is_closed() -> None:
    assert _PUBLIC_DISTRIBUTION_ENABLED is False


def test_route_is_not_in_public_allowlist() -> None:
    assert _is_engineering_public_path(
        "/public/characters/eva/avatar/avatar-v1.jpg"
    ) is False


def test_valid_request_is_blocked_until_ratification() -> None:
    response = get_public_character_avatar("eva", "avatar-v1.jpg")
    assert response.status_code == 404


def test_profile_and_asset_exist_but_stay_unpublished() -> None:
    profile = get_eva_profile()
    assert profile.identity.character_id == "eva"
    assert profile.appearance.avatar_status == "OFFICIAL_AVATAR_APPROVED"
    api_root = Path(__file__).resolve().parents[1]
    assert (api_root / profile.appearance.avatar_reference).is_file()
