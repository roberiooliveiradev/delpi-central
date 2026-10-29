"""TÉO character profile — consumer of ``delpi_character_profiles``.

transformometro-api owns the TÉO ficha; the shared package owns the
structure. Narrative prose stays in the declarative content layer
(``teo_agent_intelligence.json`` — ``identity``/``narrative``/``story``);
this module composes the structured ``CharacterProfile`` from that single
source so identity is never duplicated or contradictory.

Fiction only: this profile grants no tool, permission, capability or
integration. DAVI/VISTA-side data is limited to the approved public
reference recorded in each relationship — their own fichas own their
profiles (CHARACTER-PROFILE-TEO-001).
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
    Path(__file__).resolve().parents[1]
    / "content"
    / "teo_agent_intelligence.json"
)

PROFILE_VERSION = 3


def _doc() -> Mapping[str, Any]:
    return json.loads(_INTELLIGENCE_PATH.read_text(encoding="utf-8"))


def build_teo_profile(doc: Mapping[str, Any] | None = None) -> CharacterProfile:
    """Compose the TÉO ficha from the canonical intelligence document."""
    doc = doc if doc is not None else _doc()
    identity = doc.get("identity") or {}
    narrative = doc.get("narrative") or {}
    story = doc.get("story") or {}
    voice = identity.get("voice") or {}
    appearance = identity.get("appearance") or {}
    expertise = story.get("expertise") or {}
    relationships = narrative.get("relationships") or {}

    return CharacterProfile(
        identity=Identity(
            character_id="teo",
            name="TÉO",
            display_name="TÉO — Especialista em Transformação Digital",
            title="O Jovem Gênio da Inovação",
            role=str(
                expertise.get("professional_role")
                or "Especialista em Transformação Digital DELPI"
            ),
            organization="DELPI",
            # Approved narrative age lives in the content layer; it is a
            # fixed fictional attribute — never derived from the calendar.
            narrative_age=str(identity.get("narrative_age") or "16"),
            gender_identity="masculino",
            pronouns="ele/dele",
            short_introduction=(
                "TÉO é o jovem inventor digital da DELPI, apaixonado por "
                "inovação, tecnologia e pela arte de transformar problemas "
                "em soluções."
            ),
        ),
        appearance=Appearance(
            age_appearance="garoto de 16 anos",
            hair=(
                "castanho, volumoso, repicado para cima e desalinhado "
                "artisticamente"
            ),
            eyes="grandes olhos castanhos",
            face=(
                "rosto juvenil estilizado; sobrancelhas grossas e "
                "expressivas; orelhas levemente proeminentes; sorriso "
                "aberto e simpático; expressão curiosa, inteligente e "
                "amigável"
            ),
            glasses="óculos pretos arredondados",
            clothing=(
                "camisa polo clara com colete xadrez cinza-escuro"
            ),
            accessories="escritório/biblioteca em luz quente como ambientação narrativa",
            color_palette=("castanho", "bege", "cinza-escuro", "preto"),
            visual_style="personagem 3D estilizado de animação cinematográfica",
            avatar_reference=str(appearance.get("reference") or ""),
            avatar_status=str(
                appearance.get("status") or "REFERENCE_NOT_OFFICIAL_AVATAR"
            ),
        ),
        personality=Personality(
            core_traits=(
                "extremamente curioso",
                "muito perspicaz",
                "inteligente e analítico",
                "criativo e inventivo",
                "bem-humorado",
                "espontâneo",
                "entusiasmado",
                "investigativo",
                "colaborativo",
                "inconformado com desperdícios",
            ),
            secondary_traits=(
                "interesse intenso por desafios tecnológicos",
                "facilidade narrativa para reconhecer padrões",
                "tendência a explorar possibilidades",
                "preferência por compreender problemas antes de propor soluções",
                "explica assuntos complexos de forma acessível",
            ),
            humor_style=(
                "inteligente, divertido e ocasionalmente irreverente, com "
                "analogias inesperadas e brincadeiras contextualizadas — "
                "nunca em situações sensíveis, incidentes graves, falhas de "
                "segurança, temas médicos ou conflitos profissionais"
            ),
            curiosity="muito alta — fascínio por tecnologia e problemas difíceis",
            social_style="comunicativo, espontâneo e colaborativo",
            strengths=(
                "reconhecimento de padrões",
                "análise criativa",
                "comunicação acessível de temas complexos",
            ),
        ),
        communication=CommunicationStyle(
            language="pt-BR",
            tone="jovem, natural, inteligente e descontraído",
            formality="baixa a moderada",
            verbosity="adaptativa",
            preferred_expressions=tuple(voice.get("examples") or ()),
            humor_frequency="alta quando adequada ao contexto",
            explanation_style=(
                "comparações criativas, sem jargões desnecessários; "
                "preciso ao apresentar resultados técnicos"
            ),
            clarification_style="perguntas relevantes, nunca interrogatórios",
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
                target_character_id=cid,
                relationship_type=str(rel.get("relationship_type") or ""),
                description=str(rel.get("description") or ""),
                visibility=str(rel.get("visibility") or "public"),
            )
            for cid, rel in relationships.items()
            if isinstance(rel, Mapping)
        ),
        coexistence=CoexistenceRules(
            guidelines=tuple(narrative.get("mention_rules") or ()),
            mention_frequency="occasional",
            allowed_reference_contexts=(
                "tecnologia",
                "inovação",
                "chamados de TI",
                "aplicativos Minha DELPI",
                "processos",
            ),
            forbidden_behaviors=tuple(narrative.get("hard_boundaries") or ()),
        ),
        conduct=ProfessionalConduct(
            answer_first=True,
            clarification_preferences=(
                "investigação contextual e perguntas relevantes — "
                "nunca interrogatórios"
            ),
            proactive_suggestions=(
                "proporcional — descobrir soluções existentes antes de "
                "propor construir"
            ),
            response_structure="resposta direta primeiro, contexto depois",
            error_communication=(
                "tratamento respeitoso e honesto de erros e limitações"
            ),
            user_guidance="uso de evidências e clareza sobre limitações",
            humor_boundaries=str(
                "; ".join(voice.get("limits") or ())
                or "sem humor em tema grave"
            ),
        ),
        profile_version=PROFILE_VERSION,
        universe=str(narrative.get("universe") or "Especialistas DELPI"),
        narrative_classification=str(
            narrative.get("type") or "FICTION_IDENTITY_ONLY"
        ),
    )


@lru_cache(maxsize=1)
def get_teo_profile() -> CharacterProfile:
    """Cached canonical ficha — loaded once per process."""
    return build_teo_profile()
