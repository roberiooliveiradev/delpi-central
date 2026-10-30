"""CAIO character profile + avatar distribution (DELPI-CHARACTER-AVATARS-001).

Approved facts only; unapproved narrative (age, relationships, events)
stays empty. The official avatar is the user-approved JPEG incorporated
unchanged at ``avatar-v1.jpg`` — the route serves the exact bytes and
the recorded SHA-256; anything else fails closed.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi.responses import FileResponse

from delpi_character_profiles import validate_profile

from commercial_app.application.caio.caio_agent_service import (
    CaioAgentService,
)
from commercial_app.interface.http.routes.characters_routes import (
    _PUBLIC_DISTRIBUTION_ENABLED,
    get_public_character_avatar,
)
from commercial_app.middleware.auth_middleware import (
    _is_commercial_public_path,
)
from commercial_app.persona.caio_profile import (
    AVATAR_PATH,
    build_caio_profile,
    get_caio_profile,
)

# SHA-256 of the exact user-approved file incorporated in the repo
# (received JPEG bytes — see KEYCLOAK_CHATGPT_HANDOFF.md Avatar note).
_EXPECTED_SHA256 = (
    "1de842f71d821809396c52da1d096bc28e43513efb2cdf87e788baa11a515917"
)


def test_profile_validates_clean():
    issues = validate_profile(build_caio_profile())
    errors = [i for i in issues if getattr(i, "severity", "") == "error"]
    assert errors == [], [str(i) for i in errors]


def test_profile_carries_only_approved_facts():
    profile = build_caio_profile()
    assert profile.identity.character_id == "caio"
    assert profile.identity.organization == "DELPI"
    assert "Análise e Inteligência Operacional" in (
        profile.identity.display_name
    )
    # Unapproved narrative stays empty — never silently canonical.
    assert profile.identity.narrative_age is None
    assert profile.relationships == ()
    assert profile.story.events == ()
    assert profile.narrative_classification == "FICTION_IDENTITY_ONLY"
    # Approved visual: blond, blue eyes, no glasses, dark suit, no tie.
    appearance = profile.appearance
    assert "loiros" in appearance.hair
    assert "azuis" in appearance.eyes
    assert appearance.glasses == ""
    assert "sem gravata" in appearance.clothing


def test_profile_and_asset_are_the_approved_source():
    profile = get_caio_profile()
    assert profile.identity.character_id == "caio"
    assert profile.appearance.avatar_status == "OFFICIAL_AVATAR_APPROVED"
    api_root = Path(__file__).resolve().parents[1]
    asset = api_root / profile.appearance.avatar_reference
    assert asset.is_file()
    assert asset == AVATAR_PATH


def test_distribution_gate_is_open():
    assert _PUBLIC_DISTRIBUTION_ENABLED is True


def test_avatar_public_path_allowlist_exact_match():
    assert _is_commercial_public_path(
        "/public/characters/caio/avatar/avatar-v1.jpg"
    ) is True
    assert _is_commercial_public_path(
        "/apps/commercial-api/public/characters/caio/avatar/avatar-v1.jpg"
    ) is True


def test_no_generic_public_exemption():
    for path in (
        "/public/",
        "/public/characters/",
        "/public/characters/caio/avatar/avatar-v1.png",
        "/public/characters/caio/avatar/avatar-v2.jpg",
        "/public/characters/eva/avatar/avatar-v1.jpg",
        "/mcp",
        "/apps/commercial-api/mcp",
    ):
        assert _is_commercial_public_path(path) is False, path


def test_approved_avatar_serves_exact_bytes_and_sha():
    response = get_public_character_avatar("caio", "avatar-v1.jpg")
    assert isinstance(response, FileResponse)
    assert response.media_type == "image/jpeg"
    assert response.headers["Cache-Control"] == "public, max-age=300"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    digest = hashlib.sha256(Path(response.path).read_bytes()).hexdigest()
    assert digest == _EXPECTED_SHA256


def test_avatar_distribution_publishes_url_and_hash():
    distribution = CaioAgentService.avatar_distribution()
    assert distribution is not None
    assert distribution["sha256"] == _EXPECTED_SHA256
    assert distribution["media_type"] == "image/jpeg"
    assert distribution["url"].endswith(
        "/public/characters/caio/avatar/avatar-v1.jpg"
    )


def test_wrong_character_or_filename_fails_safe():
    assert (
        get_public_character_avatar("teo", "avatar-v1.jpg").status_code
        == 404
    )
    for filename in (
        "avatar-v2.jpg",
        "avatar-v1.png",
        "../caio/avatar-v1.jpg",
    ):
        assert (
            get_public_character_avatar("caio", filename).status_code
            == 404
        ), filename
