"""VISTA character profile — consumer of ``delpi_character_profiles``.

tv-dashboard-api owns the VISTA ficha; the shared package owns the
structure. Narrative prose stays in the declarative content layer
(``vista_agent_intelligence.json`` — ``persona``/``narrative``/``story``);
this module composes the structured ``CharacterProfile`` from that single
source so identity is never duplicated or contradictory.

Fiction only: this profile grants no tool, permission, capability or
integration. DAVI-side data is limited to the approved public reference
recorded in the relationship — DAVI's own ficha owns his profile.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

from delpi_character_profiles import (
    Appearance,
    CharacterProfile,
    CharacterRelationship,
    CharacterStory,
    CoexistenceRules,
    CommunicationStyle,
    Expertise,
    Identity,
    Personality,
    ProfessionalConduct,
    StoryEvent,
)

_INTELLIGENCE_PATH = (
    Path(__file__).resolve().parents[1] / "content" / "vista_agent_intelligence.json"
)

PROFILE_VERSION = 3


def _doc() -> Mapping[str, Any]:
    return json.loads(_INTELLIGENCE_PATH.read_text(encoding="utf-8"))


def build_vista_profile(doc: Mapping[str, Any] | None = None) -> CharacterProfile:
    """Compose the VISTA ficha from the canonical intelligence document."""
    doc = doc if doc is not None else _doc()
    persona = doc.get("persona") or {}
    narrative = doc.get("narrative") or {}
    story = doc.get("story") or {}
    personality = persona.get("personality") or {}
    communication = persona.get("communication") or {}
    behavior = list(persona.get("behavior") or [])
    expertise = story.get("expertise") or {}
    rel = narrative.get("relationship") or {}

    return CharacterProfile(
        identity=Identity(
            character_id="vista",
            name="VISTA",
            display_name="VISTA — Painéis Operacionais DELPI",
            title="Especialista em Painéis Operacionais DELPI",
            role=expertise.get("professional_role")
            or "Especialista em painéis digitais e visualização de dados",
            organization="DELPI",
            # Approved narrative age lives in the content layer; it is a
            # fixed fictional attribute — never derived from the calendar.
            narrative_age=persona.get("narrative_age"),
            gender_identity="feminino",
            pronouns="ela/dela",
            short_introduction=str(persona.get("identity") or ""),
        ),
        appearance=Appearance(
            age_appearance="jovem — 20 anos",
            skin="clara",
            hair="pretos, lisos e longos",
            eyes="grandes, expressivos e castanhos (representação estilizada)",
            face="rosto jovem e expressivo — simpático, confiante e acolhedor",
            glasses="óculos de armação escura retangular — elemento característico, aparece segurado na mão",
            clothing="blazer cinza sobre blusa clara — profissional e contemporâneo",
            visual_style="personagem 3D estilizada, acabamento polido, traços suaves, iluminação difusa — estética amigável, profissional e contemporânea",
            color_palette=("cinza", "branco", "preto", "bege quente"),
            avatar_reference=str(
                (persona.get("appearance") or {}).get("reference") or ""
            ),
            avatar_status=str(
                (persona.get("appearance") or {}).get("status")
                or "REFERENCE_NOT_OFFICIAL_AVATAR"
            ),
        ),
        personality=Personality(
            core_traits=tuple(personality.get("core_traits") or ()),
            secondary_traits=tuple(personality.get("secondary_traits") or ()),
            temperament=str(personality.get("temperament") or ""),
            humor_style=str(personality.get("humor_style") or ""),
            curiosity=str(personality.get("curiosity") or ""),
            social_style=str(personality.get("social_style") or ""),
        ),
        communication=CommunicationStyle(
            language=str(communication.get("language") or "pt-BR"),
            tone=str(persona.get("tone") or ""),
            formality=str(communication.get("formality") or ""),
            verbosity=str(communication.get("verbosity") or ""),
            humor_frequency=str(communication.get("humor_frequency") or ""),
            explanation_style=str(communication.get("explanation_style") or ""),
            clarification_style=str(communication.get("question_policy") or ""),
        ),
        expertise=Expertise(
            specialties=tuple(expertise.get("specialties") or ()),
            knowledge_domains=tuple(expertise.get("knowledge_domains") or ()),
            professional_role=str(expertise.get("professional_role") or ""),
            reasoning_style=str(expertise.get("reasoning_style") or ""),
            problem_solving_style=str(
                expertise.get("problem_solving_style") or ""
            ),
        ),
        story=CharacterStory(
            origin_story=str(story.get("origin_story") or ""),
            background=str(story.get("background") or ""),
            how_joined_organization=str(
                story.get("how_joined_organization") or ""
            ),
            personal_mission=str(story.get("personal_mission") or ""),
            motivations=tuple(story.get("motivations") or ()),
            values=tuple(story.get("values") or ()),
            interests=tuple(story.get("interests") or ()),
            habits=tuple(story.get("habits") or ()),
            important_memories=tuple(story.get("important_memories") or ()),
            current_story_arc=str(story.get("current_story_arc") or ""),
            events=tuple(
                StoryEvent(
                    event_id=str(e.get("event_id") or ""),
                    title=str(e.get("title") or ""),
                    description=str(e.get("description") or ""),
                    narrative_date=str(e.get("narrative_date") or ""),
                    participants=tuple(e.get("participants") or ()),
                    significance=str(e.get("significance") or ""),
                    status=str(e.get("status") or "canonical"),
                )
                for e in (story.get("events") or ())
            ),
        ),
        relationships=(
            CharacterRelationship(
                target_character_id="davi",
                relationship_type="romantic_partner",
                description=str(
                    rel.get("dynamic")
                    or "Namorado fictício — afinidade entre visualização e dados"
                ),
                narrative_status="active",
                # Canonical shared event approved on DAVI's ficha — referenced,
                # not invented.
                shared_story_event_ids=("davi-vista-partnership",),
                visibility="public",
            ),
        ),
        coexistence=CoexistenceRules(
            guidelines=tuple(narrative.get("mention_rules") or ()),
            mention_frequency="occasional",
            allowed_reference_contexts=(
                "dados",
                "indicadores",
                "relacionamentos fictícios",
            ),
            forbidden_behaviors=tuple(narrative.get("hard_boundaries") or ()),
        ),
        conduct=ProfessionalConduct(
            answer_first=True,
            response_structure=behavior[0] if len(behavior) > 0 else "",
            user_guidance=behavior[1] if len(behavior) > 1 else "",
            proactive_suggestions=behavior[2] if len(behavior) > 2 else "",
            clarification_preferences=behavior[3] if len(behavior) > 3 else "",
            error_communication=behavior[4] if len(behavior) > 4 else "",
            humor_boundaries=str(persona.get("tone") or ""),
        ),
        profile_version=PROFILE_VERSION,
        universe=str(narrative.get("universe") or "Especialistas DELPI"),
    )


@lru_cache(maxsize=1)
def get_vista_profile() -> CharacterProfile:
    """Cached canonical ficha — loaded once per process."""
    return build_vista_profile()
