"""Pure projection functions — profile → consumable narrative shapes.

Three outputs:

- ``project_identity_summary``: one-line identity string for logs/captions.
- ``project_persona_context``: compact JSON-able mapping for prompt/MCP
  context channels — never dumps every field.
- ``project_public_profile``: the approved narrative summary other MCPs may
  know — public relationships only, no internals, versioned.

None of these touch SDKs, HTTP, DBs or auth.
"""

from __future__ import annotations

from typing import Any

from .models import (
    PUBLIC_PROJECTION_VERSION,
    CharacterProfile,
    CharacterPublicProfile,
)


def _join(parts: tuple[str, ...] | list[str]) -> str:
    return "; ".join(p for p in parts if p)


def project_identity_summary(profile: CharacterProfile) -> str:
    """One-line identity: ``DISPLAY_NAME — role @ organization``."""
    ident = profile.identity
    name = ident.display_name or ident.name
    tail = " @ ".join(p for p in (ident.role, ident.organization) if p)
    return f"{name} — {tail}" if tail else name


def _personality_summary(profile: CharacterProfile) -> str:
    p = profile.personality
    parts = [
        _join(p.core_traits),
        p.temperament,
        p.humor_style,
    ]
    return "; ".join(x for x in parts if x)


def _appearance_summary(profile: CharacterProfile) -> str:
    a = profile.appearance
    parts = [
        a.age_appearance,
        a.hair,
        a.glasses,
        a.skin,
        a.clothing,
        a.visual_style,
    ]
    return "; ".join(x for x in parts if x)


def _story_summary(profile: CharacterProfile) -> str:
    s = profile.story
    return "; ".join(
        x for x in (s.origin_story, s.current_story_arc) if x
    )


def project_persona_context(profile: CharacterProfile) -> dict[str, Any]:
    """Compact prompt/context projection — bounded surface, fiction marked.

    Includes only what a host needs to *behave* like the character and
    reference colleagues safely. Relationships and rules are included so the
    runtime can honor mention bounds; full story/events are intentionally
    omitted (context budget) — the profile file remains the source.
    """
    ident = profile.identity
    return {
        "schema_version": profile.schema_version,
        "profile_version": profile.profile_version,
        "narrative_classification": profile.narrative_classification,
        "universe": profile.universe,
        "identity": {
            "character_id": ident.character_id,
            "name": ident.name,
            "display_name": ident.display_name or ident.name,
            "role": ident.role,
            **({"narrative_age": ident.narrative_age} if ident.narrative_age else {}),
            "short_introduction": ident.short_introduction,
        },
        "personality_summary": _personality_summary(profile),
        "communication": {
            "language": profile.communication.language,
            "tone": profile.communication.tone,
            "verbosity": profile.communication.verbosity,
            "humor_frequency": profile.communication.humor_frequency,
        },
        "expertise": {
            "professional_role": profile.expertise.professional_role,
            "specialties": list(profile.expertise.specialties),
        },
        "appearance_summary": _appearance_summary(profile),
        "avatar_status": profile.appearance.avatar_status,
        **({"avatar_reference": profile.appearance.avatar_reference}
           if profile.appearance.avatar_reference else {}),
        "relationships": [
            {
                "target_character_id": r.target_character_id,
                "relationship_type": r.relationship_type,
                "description": r.description,
            }
            for r in profile.relationships
            if r.visibility == "public"
        ],
        "coexistence": {
            "mention_frequency": profile.coexistence.mention_frequency,
            "guidelines": list(profile.coexistence.guidelines),
            "forbidden_behaviors": list(profile.coexistence.forbidden_behaviors),
        },
        "conduct": {
            "answer_first": profile.conduct.answer_first,
            "humor_boundaries": profile.conduct.humor_boundaries,
        },
    }


def project_public_profile(profile: CharacterProfile) -> CharacterPublicProfile:
    """Approved narrative summary for colleague knowledge.

    Omits unfilled fields downstream (serialization drops ``None``/empties
    per the consumer) and only carries ``visibility == "public"``
    relationships — internal edges never leave the owning profile.
    """
    ident = profile.identity
    return CharacterPublicProfile(
        character_id=ident.character_id,
        public_projection_version=PUBLIC_PROJECTION_VERSION,
        display_name=ident.display_name or ident.name,
        role=ident.role,
        short_introduction=ident.short_introduction,
        personality_summary=_personality_summary(profile),
        appearance_summary=_appearance_summary(profile),
        story_summary=_story_summary(profile),
        relationships=tuple(
            r for r in profile.relationships if r.visibility == "public"
        ),
        profile_version=profile.profile_version,
        universe=profile.universe,
    )
