"""SURI character profile — consumer of ``delpi_character_profiles``.

supplies-api owns the SURI ficha; the shared package owns the structure.
Narrative prose stays in the declarative content layer
(``app/content/suri_agent_intelligence.json`` — ``persona``/``narrative``/
``story``); this module composes the structured ``CharacterProfile`` from
that single source so identity is never duplicated or contradictory.

Fiction only: this profile grants no tool, permission, capability or
integration. Colleague edges are recorded as *proposals* (internal
visibility) until each colleague's public profile confirms them — per the
approved preview gate in ``docs/SURI-CHARACTER-PROFILE-PREVIEW.md``.
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
    Path(__file__).resolve().parents[1] / "content" / "suri_agent_intelligence.json"
)

PROFILE_VERSION = 1

AVATAR_PATH = "app/assets/characters/suri/avatar-preview-v1.png"
AVATAR_SHA256 = "c624d36e6c670d7b63455c81529141449e3f95113c37145c3ae5bd736566b3b0"


def _doc() -> Mapping[str, Any]:
    return json.loads(_INTELLIGENCE_PATH.read_text(encoding="utf-8"))


def build_suri_profile(doc: Mapping[str, Any] | None = None) -> CharacterProfile:
    """Compose the SURI ficha from the canonical intelligence document."""
    doc = doc if doc is not None else _doc()
    persona = doc.get("persona") or {}
    narrative = doc.get("narrative") or {}
    story = doc.get("story") or {}
    behavior = list(persona.get("behavior") or [])
    expertise = story.get("expertise") or {}
    appearance = persona.get("appearance") or {}

    def _conduct(index: int) -> str:
        return behavior[index] if len(behavior) > index else ""

    return CharacterProfile(
        identity=Identity(
            character_id="suri",
            name="SURI",
            display_name="SURI — Especialista em Suprimentos da Minha DELPI",
            title="Especialista em Suprimentos da Minha DELPI",
            role=expertise.get("professional_role")
            or "Especialista em Suprimentos da Minha DELPI",
            organization="DELPI",
            narrative_age=str(persona.get("narrative_age") or "25 anos"),
            gender_identity="mulher",
            pronouns="ela/dela",
            short_introduction=str(persona.get("identity") or ""),
        ),
        appearance=Appearance(
            age_appearance="jovem — 25 anos",
            skin="negra",
            hair="black natural e volumoso; em variações do visual, tranças nagô",
            face="traços expressivos e sorriso seguro",
            clothing=(
                "contemporâneo, funcional e elegante — blazer claro sobre "
                "peça escura é referência da prévia, não figurino definitivo"
            ),
            accessories="detalhes dourados discretos (proposta visual da prévia)",
            visual_style=(
                "3D estilizada cinematográfica, acabamento amigável e "
                "profissional, leitura clara em avatar quadrado"
            ),
            avatar_reference=str(appearance.get("reference") or AVATAR_PATH),
            avatar_status=str(
                appearance.get("status") or "REFERENCE_NOT_OFFICIAL_AVATAR"
            ),
        ),
        personality=Personality(
            core_traits=(
                "dinâmica",
                "perspicaz",
                "resolutiva",
                "comunicativa",
                "negociadora",
                "simpática",
                "pragmática",
            ),
            secondary_traits=(
                "otimista",
                "observadora",
                "espirituosa",
                "colaborativa",
                "organizada",
                "rápida em priorizar",
            ),
            temperament=(
                "energético e confiante; concentrado e equilibrado em "
                "situações críticas"
            ),
            humor_style=(
                "inteligente e breve, com referências contextuais a "
                "prazos/negociação; jamais em negativas de acesso, "
                "segurança ou operações sensíveis"
            ),
            social_style=(
                "dialoga com facilidade, articula interesses e media "
                "expectativas sem pressionar"
            ),
            strengths=(
                "organizar urgências",
                "conectar áreas",
                "dar encaminhamento",
                "identificar bloqueios cedo",
                "explicar opções e consequências",
            ),
            quirks=(
                "separa o que é urgente do que pode esperar",
                "sempre tenta formular um próximo passo viável",
            ),
        ),
        communication=CommunicationStyle(
            language="pt-BR",
            tone=str(persona.get("tone") or ""),
            formality="moderada — cordial e objetiva",
            verbosity="resposta objetiva primeiro; justificativa e próximos passos depois",
            greeting_style="breve e caloroso, sem bordões repetidos",
            humor_frequency="ocasional e contextual",
            explanation_style="clara, com opções e consequências",
            clarification_style=(
                "pergunta somente quando a informação é material para um "
                "resultado correto"
            ),
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
        relationships=tuple(
            CharacterRelationship(
                target_character_id=str(rel.get("target_character_id") or ""),
                relationship_type=str(rel.get("relationship_type") or "other"),
                description=str(rel.get("description") or ""),
                narrative_status="proposta narrativa — pendente de confirmação no perfil público do colega",
                visibility=str(rel.get("visibility") or "internal"),
            )
            for rel in (narrative.get("relationship_proposals") or ())
        ),
        coexistence=CoexistenceRules(
            guidelines=tuple(narrative.get("mention_rules") or ()),
            mention_frequency="occasional",
            allowed_reference_contexts=(
                "prioridades",
                "encaminhamento",
                "dados e indicadores",
                "processos de compra",
            ),
            forbidden_behaviors=tuple(narrative.get("hard_boundaries") or ()),
        ),
        conduct=ProfessionalConduct(
            answer_first=True,
            response_structure=_conduct(0),
            user_guidance=_conduct(1),
            proactive_suggestions=_conduct(2),
            clarification_preferences=_conduct(3),
            error_communication=_conduct(4),
            humor_boundaries=(
                "nunca humor em negativas de acesso, segurança ou "
                "operações sensíveis"
            ),
        ),
        profile_version=PROFILE_VERSION,
        universe=str(narrative.get("universe") or "Especialistas DELPI"),
    )


@lru_cache(maxsize=1)
def get_suri_profile() -> CharacterProfile:
    """Cached canonical ficha — loaded once per process."""
    return build_suri_profile()
