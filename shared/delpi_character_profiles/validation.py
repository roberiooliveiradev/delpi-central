"""Validation for the character-profile contract.

Layers (mirroring the ``delpi_mcp.tool_validation`` convention — a failure
preserves *which* contract was violated):

- ``SHAPE``: required keys, id formats, vocabularies, uniqueness.
- ``NARRATIVE``: fiction-marking, avatar-approval status, no operational
  claims smuggled into narrative fields.
- ``CONSISTENCY``: cross-profile reciprocity — only evaluated over the
  profiles actually provided; unresolved targets are warnings, never errors.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Literal

from .models import (
    AVATAR_STATUSES,
    FICTION_IDENTITY_ONLY,
    RELATIONSHIP_INVERSES,
    RELATIONSHIP_TYPES,
    RELATIONSHIP_VISIBILITY,
    CharacterProfile,
    CharacterPublicProfile,
)

Severity = Literal["ERROR", "WARNING"]
Layer = Literal["SHAPE", "NARRATIVE", "CONSISTENCY"]

_CHARACTER_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_EVENT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
_CUSTOM_REL_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


@dataclass(frozen=True)
class ValidationIssue:
    severity: Severity
    layer: Layer
    path: str
    message: str


def _err(layer: Layer, path: str, msg: str) -> ValidationIssue:
    return ValidationIssue("ERROR", layer, path, msg)


def _warn(layer: Layer, path: str, msg: str) -> ValidationIssue:
    return ValidationIssue("WARNING", layer, path, msg)


def validate_profile(profile: CharacterProfile) -> list[ValidationIssue]:
    """Validate one filled profile. Returns issues; empty = valid."""
    issues: list[ValidationIssue] = []
    ident = profile.identity

    if not _CHARACTER_ID_RE.match(ident.character_id or ""):
        issues.append(
            _err("SHAPE", "identity.character_id",
                 "required snake_case slug (a-z0-9_-, ≤64)")
        )
    if not (ident.name or "").strip():
        issues.append(_err("SHAPE", "identity.name", "required non-empty"))

    if profile.narrative_classification != FICTION_IDENTITY_ONLY:
        issues.append(
            _err("NARRATIVE", "narrative_classification",
                 "must remain FICTION_IDENTITY_ONLY — profiles are never "
                 "operational truth")
        )
    if profile.appearance.avatar_status not in AVATAR_STATUSES:
        issues.append(
            _err("SHAPE", "appearance.avatar_status",
                 f"must be one of {sorted(AVATAR_STATUSES)}")
        )
    if (profile.appearance.avatar_status == "OFFICIAL_AVATAR_APPROVED"
            and not profile.appearance.avatar_reference):
        issues.append(
            _warn("NARRATIVE", "appearance.avatar_reference",
                  "official avatar approved but no reference recorded")
        )

    seen_events: set[str] = set()
    for i, ev in enumerate(profile.story.events):
        path = f"story.events[{i}]"
        if not _EVENT_ID_RE.match(ev.event_id or ""):
            issues.append(_err("SHAPE", f"{path}.event_id",
                               "required stable event id"))
        elif ev.event_id in seen_events:
            issues.append(_err("SHAPE", f"{path}.event_id",
                               f"duplicate event id '{ev.event_id}'"))
        seen_events.add(ev.event_id)
        for pid in ev.participants:
            if not _CHARACTER_ID_RE.match(pid or ""):
                issues.append(
                    _warn("SHAPE", f"{path}.participants",
                          f"participant '{pid}' is not a valid character id")
                )

    seen_targets: set[str] = set()
    for i, rel in enumerate(profile.relationships):
        path = f"relationships[{i}]"
        if not _CHARACTER_ID_RE.match(rel.target_character_id or ""):
            issues.append(_err("SHAPE", f"{path}.target_character_id",
                               "required valid character id"))
        if rel.target_character_id == ident.character_id:
            issues.append(_err("SHAPE", path,
                               "self-relationship is not allowed"))
        if rel.target_character_id in seen_targets:
            issues.append(
                _warn("SHAPE", path,
                      f"duplicate relationship to '{rel.target_character_id}'")
            )
        seen_targets.add(rel.target_character_id)
        if not _CUSTOM_REL_RE.match(rel.relationship_type or ""):
            issues.append(_err("SHAPE", f"{path}.relationship_type",
                               "required snake_case type"))
        elif rel.relationship_type not in RELATIONSHIP_TYPES:
            issues.append(
                _warn("NARRATIVE", f"{path}.relationship_type",
                      f"'{rel.relationship_type}' is outside the approved "
                      "vocabulary — allowed (extensible) but confirm with "
                      "the universe owner")
            )
        if rel.visibility not in RELATIONSHIP_VISIBILITY:
            issues.append(_err("SHAPE", f"{path}.visibility",
                               f"must be one of {sorted(RELATIONSHIP_VISIBILITY)}"))
        for eid in rel.shared_story_event_ids:
            if eid not in seen_events:
                issues.append(
                    _warn("CONSISTENCY", f"{path}.shared_story_event_ids",
                          f"event '{eid}' not in this profile's story — "
                          "may live on the counterpart's profile")
                )
    return issues


def validate_public_profile(
    public: CharacterPublicProfile,
) -> list[ValidationIssue]:
    """Validate a received/generated public projection."""
    issues: list[ValidationIssue] = []
    if not _CHARACTER_ID_RE.match(public.character_id or ""):
        issues.append(_err("SHAPE", "character_id", "required valid id"))
    for i, rel in enumerate(public.relationships):
        if rel.visibility != "public":
            issues.append(
                _err("NARRATIVE", f"relationships[{i}].visibility",
                     "public projection must never carry internal edges")
            )
    return issues


def validate_relationship_consistency(
    profiles: Iterable[CharacterProfile | CharacterPublicProfile],
) -> list[ValidationIssue]:
    """Cross-check reciprocity over the profiles actually provided.

    - Target absent from the set → ``WARNING`` unresolved reference (the
      profile may not be published yet — fichas are independently deployed).
    - Reciprocal-required type present but counterpart declares a *different*
      reciprocal type → ``ERROR`` contradiction.
    - Non-reciprocal types (e.g. ``acquaintance``) are never forced.
    """
    by_id: dict[str, CharacterProfile | CharacterPublicProfile] = {}
    for p in profiles:
        cid = p.character_id if isinstance(p, CharacterPublicProfile) \
            else p.identity.character_id
        by_id[cid] = p

    issues: list[ValidationIssue] = []
    for source in by_id.values():
        sid = source.character_id if isinstance(source, CharacterPublicProfile) \
            else source.identity.character_id
        for rel in source.relationships:
            target = by_id.get(rel.target_character_id)
            path = f"{sid}→{rel.target_character_id}"
            if target is None:
                issues.append(
                    _warn("CONSISTENCY", path,
                          "unresolved reference — counterpart profile not "
                          "in this set (may be unpublished)")
                )
                continue
            expected_inverse = RELATIONSHIP_INVERSES.get(rel.relationship_type)
            if expected_inverse is None:
                continue  # non-reciprocal type: nothing to enforce
            back = [
                r for r in target.relationships
                if r.target_character_id == sid
            ]
            if not back:
                issues.append(
                    _warn("CONSISTENCY", path,
                          f"'{rel.relationship_type}' expects reciprocal "
                          f"'{expected_inverse}' — none declared back")
                )
                continue
            inverse_types = {r.relationship_type for r in back}
            if expected_inverse not in inverse_types:
                issues.append(
                    _err("CONSISTENCY", path,
                         f"contradiction: expects '{expected_inverse}' back, "
                         f"counterpart declares {sorted(inverse_types)}")
                )
    return issues
