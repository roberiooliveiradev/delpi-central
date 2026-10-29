"""Model construction, optionality, immutability and scalability."""

from __future__ import annotations

import dataclasses

import pytest

from delpi_character_profiles import (
    FICTION_IDENTITY_ONLY,
    SCHEMA_VERSION,
    CharacterProfile,
    Identity,
)


def test_minimal_profile_constructs() -> None:
    profile = CharacterProfile(identity=Identity(character_id="x", name="X"))
    assert profile.schema_version == SCHEMA_VERSION
    assert profile.narrative_classification == FICTION_IDENTITY_ONLY
    assert profile.universe == "Especialistas DELPI"
    assert profile.relationships == ()
    assert profile.story.events == ()


def test_identity_accepts_absent_demographics() -> None:
    ident = Identity(character_id="x", name="X")
    assert ident.narrative_age is None
    assert ident.gender_identity is None
    assert ident.pronouns is None


def test_frozen_immutability(alpha_profile) -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        alpha_profile.identity.name = "other"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        alpha_profile.profile_version = 9  # type: ignore[misc]


def test_profiles_are_independent_instances(alpha_profile, beta_profile) -> None:
    assert alpha_profile.identity.character_id == "alpha"
    assert beta_profile.identity.character_id == "beta"
    # Mutating fixture-independent copies does not leak between profiles.
    other = dataclasses.replace(beta_profile, profile_version=2)
    assert beta_profile.profile_version == 1 and other.profile_version == 2


def test_many_characters_without_contract_changes() -> None:
    """Scalability: N generic characters need zero model changes."""
    profiles = [
        CharacterProfile(
            identity=Identity(character_id=f"char-{i:03d}", name=f"CHAR{i}"),
            profile_version=i,
        )
        for i in range(10)
    ]
    ids = {p.identity.character_id for p in profiles}
    assert len(ids) == 10


def test_story_event_evolves_without_schema_change(alpha_profile) -> None:
    new_event = dataclasses.replace(
        alpha_profile.story.events[0], title="Renamed event"
    )
    story2 = dataclasses.replace(
        alpha_profile.story, events=alpha_profile.story.events + (new_event,)
    )
    assert len(story2.events) == 3
