"""Generic fictional fixtures — two invented specialists, no real data."""

from __future__ import annotations

import pytest

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


@pytest.fixture()
def alpha_profile() -> CharacterProfile:
    """Fictional 'ALPHA' — an inventory-analyst specialist."""
    return CharacterProfile(
        identity=Identity(
            character_id="alpha",
            name="ALPHA",
            display_name="ALPHA — Especialista Fictícia de Estoques",
            role="especialista em dados de estoque (ficção de teste)",
            organization="DELPI",
            narrative_age="~25",
            gender_identity="feminino",
            pronouns="ela/dela",
            short_introduction="Analista curiosa de inventário — personagem de teste.",
        ),
        appearance=Appearance(
            age_appearance="jovem",
            hair="castanho ondulado",
            clothing="casual tecnológico, tons de verde",
            avatar_status="REFERENCE_NOT_OFFICIAL_AVATAR",
        ),
        personality=Personality(
            core_traits=("curiosa", "metódica"),
            humor_style="seco, ocasional",
            quirks=("anota contagens em guardanapos",),
        ),
        communication=CommunicationStyle(
            language="pt-BR", tone="objetivo e leve", humor_frequency="baixa"
        ),
        expertise=Expertise(
            specialties=("inventário", "saldos"), professional_role="analista"
        ),
        story=CharacterStory(
            origin_story="Criada durante a onda de digitalização fictícia.",
            current_story_arc="Aprendendo a confiar nos dados de campo.",
            events=(
                StoryEvent(
                    event_id="alpha-origin",
                    title="Ativação da ALPHA",
                    participants=("alpha",),
                ),
                StoryEvent(
                    event_id="alpha-beta-first-meeting",
                    title="Primeiro encontro ALPHA × BETA",
                    participants=("alpha", "beta"),
                    significance="início da parceria narrativa",
                ),
            ),
        ),
        relationships=(
            CharacterRelationship(
                target_character_id="beta",
                relationship_type="friendship",
                description="Amiga fictícia da ALPHA",
                shared_story_event_ids=("alpha-beta-first-meeting",),
            ),
            CharacterRelationship(
                target_character_id="gamma_unpublished",
                relationship_type="acquaintance",
                description="Conhecida ainda sem ficha publicada",
            ),
            CharacterRelationship(
                target_character_id="delta",
                relationship_type="narrative_partnership",
                description="Parceria interna não pública",
                visibility="internal",
            ),
        ),
        coexistence=CoexistenceRules(
            mention_frequency="occasional",
            guidelines=("mencionar BETA só em contexto de inventário visual",),
            forbidden_behaviors=("inventar eventos compartilhados",),
        ),
        conduct=ProfessionalConduct(answer_first=True),
    )


@pytest.fixture()
def beta_profile() -> CharacterProfile:
    """Fictional 'BETA' — a dashboards specialist, ALPHA's friend."""
    return CharacterProfile(
        identity=Identity(
            character_id="beta",
            name="BETA",
            display_name="BETA — Especialista Fictício de Painéis",
            role="especialista em visualização (ficção de teste)",
            organization="DELPI",
        ),
        relationships=(
            CharacterRelationship(
                target_character_id="alpha",
                relationship_type="friendship",
                description="Amiga fictícia do BETA",
            ),
        ),
    )
