"""SURI character-profile contract tests (S2).

Proves: ficha compõe do content layer, valida zero ERROR no contrato
shared, projeções funcionam, avatar real existe e confere SHA-256, e
nenhum campo narrativo vaza grant operacional.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from delpi_character_profiles import (
    FICTION_IDENTITY_ONLY,
    project_identity_summary,
    project_persona_context,
    project_public_profile,
    public_profile_from_dict,
    validate_profile,
    validate_public_profile,
)

from app.persona.suri_profile import (
    AVATAR_PATH,
    AVATAR_SHA256,
    build_suri_profile,
    get_suri_profile,
)

APP_ROOT = Path(__file__).resolve().parents[2] / "app"


def _errors(issues):
    return [i for i in issues if i.severity == "ERROR"]


def test_profile_builds_and_validates_zero_errors():
    profile = build_suri_profile()
    assert profile.identity.character_id == "suri"
    assert profile.narrative_classification == FICTION_IDENTITY_ONLY
    assert _errors(validate_profile(profile)) == []


def test_identity_fields_match_approved_preview():
    profile = build_suri_profile()
    ident = profile.identity
    assert ident.name == "SURI"
    assert ident.narrative_age == "25 anos"
    assert ident.gender_identity == "mulher"
    assert ident.pronouns == "ela/dela"
    assert ident.organization == "DELPI"


def test_avatar_reference_is_official_and_file_matches_sha256():
    profile = build_suri_profile()
    assert profile.appearance.avatar_status == "OFFICIAL_AVATAR_APPROVED"
    avatar_file = APP_ROOT / "assets" / "characters" / "suri" / "avatar-preview-v1.png"
    assert avatar_file.is_file()
    assert (
        hashlib.sha256(avatar_file.read_bytes()).hexdigest() == AVATAR_SHA256
    )
    assert profile.appearance.avatar_reference == AVATAR_PATH


def test_relationships_are_internal_proposals_only():
    profile = build_suri_profile()
    assert profile.relationships, "expected colleague proposals"
    for rel in profile.relationships:
        assert rel.visibility == "internal"
        assert "proposta" in rel.narrative_status


def test_projections_work():
    profile = build_suri_profile()
    summary = project_identity_summary(profile)
    assert "SURI" in summary
    context = project_persona_context(profile)
    assert context.get("character_id") == "suri" or "SURI" in json.dumps(
        context, ensure_ascii=False
    )
    public = project_public_profile(profile)
    assert _errors(validate_public_profile(public)) == []
    # internal-visibility relationships must not leak to public projection
    assert all(r.visibility != "internal" for r in public.relationships)


def test_public_profile_file_validates():
    raw = json.loads(
        (APP_ROOT / "content" / "suri_public_profile.json").read_text(
            encoding="utf-8"
        )
    )
    public = public_profile_from_dict(raw)
    assert public.character_id == "suri"
    assert _errors(validate_public_profile(public)) == []


def test_no_operational_grants_in_narrative_fields():
    profile = build_suri_profile()
    blob = json.dumps(
        {
            "intro": profile.identity.short_introduction,
            "story": profile.story.origin_story,
            "personality": profile.personality.core_traits,
        },
        ensure_ascii=False,
    ).lower()
    for forbidden in ("supplies.access", "permission", "mcp:tools", "scope"):
        assert forbidden not in blob


def test_cached_profile_is_same_instance():
    assert get_suri_profile() is get_suri_profile()
