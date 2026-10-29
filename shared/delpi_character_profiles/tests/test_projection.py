"""Projection outputs: identity line, persona context, public profile."""

from __future__ import annotations

import json

from delpi_character_profiles import (
    PUBLIC_PROJECTION_VERSION,
    CharacterProfile,
    Identity,
    project_identity_summary,
    project_persona_context,
    project_public_profile,
)


def test_identity_summary(alpha_profile) -> None:
    summary = project_identity_summary(alpha_profile)
    assert "ALPHA" in summary and "estoque" in summary


def test_identity_summary_falls_back_to_name() -> None:
    p = CharacterProfile(identity=Identity(character_id="x", name="X Only"))
    assert project_identity_summary(p) == "X Only"


def test_persona_context_is_compact_and_marked(alpha_profile) -> None:
    ctx = project_persona_context(alpha_profile)
    assert ctx["narrative_classification"] == "FICTION_IDENTITY_ONLY"
    assert ctx["identity"]["character_id"] == "alpha"
    assert ctx["avatar_status"] == "REFERENCE_NOT_OFFICIAL_AVATAR"
    # Compact: full story/events intentionally absent from context budget.
    assert "events" not in json.dumps(ctx)
    assert "origin_story" not in json.dumps(ctx)


def test_persona_context_omits_internal_relationships(alpha_profile) -> None:
    ctx = project_persona_context(alpha_profile)
    targets = {r["target_character_id"] for r in ctx["relationships"]}
    assert "beta" in targets and "delta" not in targets


def test_persona_context_is_json_serializable(alpha_profile) -> None:
    json.dumps(project_persona_context(alpha_profile), ensure_ascii=False)


def test_public_profile_contents(alpha_profile) -> None:
    public = project_public_profile(alpha_profile)
    assert public.character_id == "alpha"
    assert public.public_projection_version == PUBLIC_PROJECTION_VERSION
    assert public.display_name.startswith("ALPHA")
    assert public.personality_summary
    assert public.story_summary
    assert {r.target_character_id for r in public.relationships} == {
        "beta",
        "gamma_unpublished",
    }


def test_public_profile_contains_no_operational_fields(alpha_profile) -> None:
    """The public projection must never carry tools/permissions/credentials."""
    from delpi_character_profiles import public_profile_to_dict

    data = public_profile_to_dict(project_public_profile(alpha_profile))
    blob = json.dumps(data).lower()
    for forbidden in ("permission", "scope", "token", "credential",
                      "tool", "endpoint", "password", "secret"):
        assert forbidden not in blob
