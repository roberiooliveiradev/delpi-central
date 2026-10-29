"""Validation: shape, narrative policy and cross-profile consistency."""

from __future__ import annotations

import dataclasses

from delpi_character_profiles import (
    CharacterProfile,
    CharacterRelationship,
    Identity,
    project_public_profile,
    validate_profile,
    validate_public_profile,
    validate_relationship_consistency,
)


def _errors(issues):
    return [i for i in issues if i.severity == "ERROR"]


def test_valid_profile_has_no_errors(alpha_profile) -> None:
    issues = validate_profile(alpha_profile)
    assert _errors(issues) == []


def test_character_id_required_and_shaped() -> None:
    bad = CharacterProfile(
        identity=Identity(character_id="Bad ID!", name="Bad")
    )
    assert any(i.path == "identity.character_id" for i in validate_profile(bad))


def test_fiction_marker_is_enforced(alpha_profile) -> None:
    bad = dataclasses.replace(
        alpha_profile, narrative_classification="OPERATIONAL_TRUTH"
    )
    issues = validate_profile(bad)
    assert any(
        i.layer == "NARRATIVE" and i.severity == "ERROR" for i in issues
    )


def test_self_relationship_rejected(alpha_profile) -> None:
    bad = dataclasses.replace(
        alpha_profile,
        relationships=alpha_profile.relationships
        + (CharacterRelationship(
            target_character_id="alpha", relationship_type="friendship"),),
    )
    assert any("self" in i.message for i in validate_profile(bad))


def test_unknown_relationship_type_warns_not_fails(alpha_profile) -> None:
    prof = dataclasses.replace(
        alpha_profile,
        relationships=alpha_profile.relationships
        + (CharacterRelationship(
            target_character_id="omega",
            relationship_type="space_penpal"),),
    )
    issues = validate_profile(prof)
    assert _errors(issues) == []
    assert any(
        i.severity == "WARNING" and "vocabulary" in i.message for i in issues
    )


def test_unresolved_target_is_warning(alpha_profile, beta_profile) -> None:
    """alpha→gamma_unpublished has no published profile: warning, not error."""
    issues = validate_relationship_consistency([alpha_profile, beta_profile])
    unresolved = [
        i for i in issues
        if i.severity == "WARNING" and "unresolved" in i.message
    ]
    assert any("gamma_unpublished" in i.path for i in unresolved)
    assert _errors(issues) == []


def test_reciprocity_passes_when_both_sides_match(
    alpha_profile, beta_profile
) -> None:
    issues = validate_relationship_consistency([alpha_profile, beta_profile])
    friendship_issues = [
        i for i in issues if "alpha→beta" in i.path or "beta→alpha" in i.path
    ]
    assert _errors(friendship_issues) == []


def test_reciprocity_contradiction_is_error(alpha_profile) -> None:
    """ALPHA declares friendship to BETA; BETA declares rivalry back."""
    bad_beta = dataclasses.replace(
        CharacterProfile(
            identity=Identity(character_id="beta", name="BETA"),
            relationships=(
                CharacterRelationship(
                    target_character_id="alpha",
                    relationship_type="friendly_rivalry",
                ),
            ),
        )
    )
    issues = validate_relationship_consistency([alpha_profile, bad_beta])
    assert any(
        i.severity == "ERROR" and "contradiction" in i.message
        for i in issues
    )


def test_public_profile_rejects_internal_edge(alpha_profile) -> None:
    public = project_public_profile(alpha_profile)
    assert _errors(validate_public_profile(public)) == []
    internal = CharacterRelationship(
        target_character_id="delta",
        relationship_type="narrative_partnership",
        visibility="internal",
    )
    bad = dataclasses.replace(
        public, relationships=public.relationships + (internal,)
    )
    assert any(
        i.layer == "NARRATIVE" and i.severity == "ERROR"
        for i in validate_public_profile(bad)
    )


def test_duplicate_event_id_rejected(alpha_profile) -> None:
    story = dataclasses.replace(
        alpha_profile.story,
        events=alpha_profile.story.events + (alpha_profile.story.events[0],),
    )
    bad = dataclasses.replace(alpha_profile, story=story)
    assert any("duplicate event id" in i.message for i in validate_profile(bad))
