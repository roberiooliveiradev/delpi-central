"""Serialization round-trip, determinism and version compatibility."""

from __future__ import annotations

import json

import pytest

from delpi_character_profiles import (
    IncompatibleVersionError,
    check_schema_compatibility,
    dumps_deterministic,
    profile_from_dict,
    profile_to_dict,
    profile_to_json,
    project_public_profile,
    public_profile_from_dict,
    public_profile_to_dict,
    public_profile_to_json,
)


def test_profile_round_trip(alpha_profile) -> None:
    data = profile_to_dict(alpha_profile)
    rebuilt = profile_from_dict(data)
    assert rebuilt == alpha_profile


def test_public_profile_round_trip(alpha_profile) -> None:
    public = project_public_profile(alpha_profile)
    data = public_profile_to_dict(public)
    assert public_profile_from_dict(data) == public


def test_none_fields_omitted_for_compactness() -> None:
    from delpi_character_profiles import CharacterProfile, Identity

    data = profile_to_dict(
        CharacterProfile(identity=Identity(character_id="x", name="X"))
    )
    assert "narrative_age" not in json.dumps(data)
    assert data["identity"]["character_id"] == "x"


def test_tuples_serialize_as_lists_and_rebuild(alpha_profile) -> None:
    data = profile_to_dict(alpha_profile)
    assert isinstance(data["personality"]["core_traits"], list)
    rebuilt = profile_from_dict(data)
    assert isinstance(rebuilt.personality.core_traits, tuple)


def test_deterministic_output(alpha_profile) -> None:
    j1 = profile_to_json(alpha_profile)
    j2 = profile_to_json(alpha_profile)
    assert j1 == j2
    # Key order is sorted — position of a known late key > early key.
    assert j1.index('"universe"') > j1.index('"identity"')


def test_unknown_fields_tolerated_forward_compat(alpha_profile) -> None:
    data = profile_to_dict(alpha_profile)
    data["future_optional_field"] = "added by schema v2"
    rebuilt = profile_from_dict(data)  # non-strict: ignores
    assert rebuilt == alpha_profile
    with pytest.raises(ValueError, match="unknown fields"):
        profile_from_dict(data, strict=True)


def test_unsupported_schema_version_fails_explicitly(alpha_profile) -> None:
    data = profile_to_dict(alpha_profile)
    data["schema_version"] = 99
    with pytest.raises(IncompatibleVersionError):
        profile_from_dict(data)


def test_unsupported_public_version_fails_explicitly(alpha_profile) -> None:
    data = public_profile_to_dict(project_public_profile(alpha_profile))
    data["public_projection_version"] = 0
    with pytest.raises(IncompatibleVersionError):
        public_profile_from_dict(data)


def test_compatibility_check_reports_axis() -> None:
    ok = check_schema_compatibility(1)
    bad = check_schema_compatibility(2)
    assert ok.status == "SUPPORTED" and bad.status == "UNSUPPORTED"
    assert bad.axis == "schema" and "2" in bad.message


def test_public_projection_carries_no_internal_relationships(
    alpha_profile,
) -> None:
    public = project_public_profile(alpha_profile)
    ids = {r.target_character_id for r in public.relationships}
    assert "delta" not in ids  # internal edge never leaves the profile
    assert "beta" in ids


def test_deterministic_bytes_for_golden_artifacts(alpha_profile) -> None:
    blob = dumps_deterministic(
        public_profile_to_dict(project_public_profile(alpha_profile))
    )
    assert blob == public_profile_to_json(
        project_public_profile(alpha_profile)
    )
