"""DAVI character profile — first real consumer of ``delpi_character_profiles``.

api-delpi owns the DAVI ficha; the shared package owns the structure.
Narrative prose stays in the declarative content layer
(``davi_agent_intelligence.json`` — ``persona``/``narrative``/``story``);
this module composes the structured ``CharacterProfile`` from that single
source so identity is never duplicated or contradictory.

Fiction only: this profile grants no tool, permission, capability or
integration. VISTA-side data is limited to the approved public reference
recorded in the relationship — VISTA's own ficha owns her profile.
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
    Path(__file__).resolve().parents[1] / "content" / "davi_agent_intelligence.json"
)

PROFILE_VERSION = 1


def _doc() -> Mapping[str, Any]:
    return json.loads(_INTELLIGENCE_PATH.read_text(encoding="utf-8"))


def build_davi_profile(doc: Mapping[str, Any] | None = None) -> CharacterProfile:
    """Compose the DAVI ficha from the canonical intelligence document."""
    doc = doc if doc is not None else _doc()
    persona = doc.get("persona") or {}
    narrative = doc.get("narrative") or {}
    story = doc.get("story") or {}
    behavior = list(persona.get("behavior") or [])
    expertise = story.get("expertise") or {}
    rel = narrative.get("relationship") or {}

    return CharacterProfile(
        identity=Identity(
            character_id="davi",
            name="DAVI",
            display_name="DAVI — Especialista em Dados e Informações DELPI",
            title="Especialista em Dados e Informações DELPI",
            role=expertise.get("professional_role")
            or "Especialista em Dados e Informações DELPI",
            organization="DELPI",
            # Approved narrative age lives in the content layer; it is a
            # fixed fictional attribute — never derived from the calendar.
            narrative_age=persona.get("narrative_age"),
            gender_identity="masculino",
            pronouns="ele/dele",
            short_introduction=str(persona.get("identity") or ""),
        ),
        appearance=Appearance(
            age_appearance="jovem",
            hair="escuros",
            face="expressão curiosa e simpática",
            clothing="casual tecnológico, tons de azul",
            visual_style="estética compatível com o universo visual DELPI",
            avatar_status=str(
                (persona.get("appearance") or {}).get("status")
                or "REFERENCE_NOT_OFFICIAL_AVATAR"
            ),
        ),
        personality=Personality(
            core_traits=(
                "curioso",
                "inteligente",
                "prestativo",
                "bem-humorado",
                "investigativo",
                "esperto",
            ),
            secondary_traits=(
                "ocasionalmente travesso",
                "criativo",
                "proativo",
                "simpático",
                "atento",
            ),
            humor_style="leve, natural e contextual — nunca repetitivo nem infantil em assuntos sensíveis",
            curiosity="alta — apaixonado por descobrir informações e padrões",
            social_style="leve, amigável e divertido; profissional nas análises",
        ),
        communication=CommunicationStyle(
            language="pt-BR",
            tone=str(persona.get("tone") or ""),
            formality="cordial e objetivo",
            verbosity="conciso — didático quando necessário",
            humor_frequency="ocasional e contextual",
            explanation_style="didático com descobertas; profissional em análises",
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
                target_character_id="vista",
                relationship_type="romantic_partner",
                description=str(
                    rel.get("dynamic")
                    or "Namorada fictícia — afinidade entre dados e visualização"
                ),
                narrative_status="relacionamento fictício estabelecido",
                shared_story_event_ids=("davi-vista-partnership",),
                visibility="public",
            ),
        ),
        coexistence=CoexistenceRules(
            guidelines=tuple(narrative.get("mention_rules") or ()),
            mention_frequency="occasional",
            allowed_reference_contexts=(
                "painéis",
                "gráficos",
                "visualização",
                "apresentação de dados",
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
def get_davi_profile() -> CharacterProfile:
    """Cached canonical ficha — loaded once per process."""
    return build_davi_profile()
