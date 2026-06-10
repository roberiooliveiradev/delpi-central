# app/domain/portal_tour/portal_tour_achievement_catalog.py

from dataclasses import dataclass

from app.domain.portal_tour.portal_tour_availability_service import quests_by_category
from app.domain.portal_tour.portal_tour_quest_catalog import (
    CATEGORY_LABELS,
    PortalTourQuestDefinition,
)


@dataclass(frozen=True)
class PortalTourAchievementDefinition:
    id: str
    title: str
    description: str
    kind: str
    quest_ids: tuple[str, ...] = ()
    milestone_percent: int | None = None


def _required_quest_ids_in_category(
    available_quests: list[PortalTourQuestDefinition],
    category: str,
) -> tuple[str, ...]:
    return tuple(
        quest.id
        for quest in available_quests
        if quest.category == category and not quest.optional
    )


def _category_achievements(
    available_quests: list[PortalTourQuestDefinition],
) -> list[PortalTourAchievementDefinition]:
    items: list[PortalTourAchievementDefinition] = []
    grouped = quests_by_category(available_quests)

    for category, quests in grouped.items():
        required_ids = _required_quest_ids_in_category(available_quests, category)
        if not required_ids:
            continue

        label = CATEGORY_LABELS.get(category, category)
        items.append(
            PortalTourAchievementDefinition(
                id=f"category-{category}",
                title=f"Explorador — {label}",
                description=f"Concluiu todos os desafios obrigatórios de {label}.",
                kind="category",
                quest_ids=required_ids,
            )
        )

    return items


def get_portal_tour_achievement_catalog(
    available_quests: list[PortalTourQuestDefinition],
) -> list[PortalTourAchievementDefinition]:
    """Conquistas derivadas do catálogo disponível ao usuário."""
    available_ids = {quest.id for quest in available_quests}

    catalog: list[PortalTourAchievementDefinition] = [
        *_category_achievements(available_quests),
        PortalTourAchievementDefinition(
            id="quest-first-favorite",
            title="Primeiro favorito",
            description="Interagiu com favoritos na barra lateral.",
            kind="quest",
            quest_ids=("sidebar-favorites",),
        ),
        PortalTourAchievementDefinition(
            id="quest-pin-master",
            title="App fixado",
            description="Fixou um app no catálogo.",
            kind="quest",
            quest_ids=("pin-app",),
        ),
        PortalTourAchievementDefinition(
            id="milestone-25",
            title="Curioso",
            description="Alcançou 25% do tour do portal.",
            kind="milestone",
            milestone_percent=25,
        ),
        PortalTourAchievementDefinition(
            id="milestone-50",
            title="No meio do caminho",
            description="Alcançou 50% do tour do portal.",
            kind="milestone",
            milestone_percent=50,
        ),
        PortalTourAchievementDefinition(
            id="milestone-75",
            title="Quase lá",
            description="Alcançou 75% do tour do portal.",
            kind="milestone",
            milestone_percent=75,
        ),
        PortalTourAchievementDefinition(
            id="tour-master",
            title="Mestre DELPI",
            description="Concluiu a exploração completa do portal.",
            kind="tour_complete",
        ),
    ]

    return [
        item
        for item in catalog
        if item.kind in {"milestone", "tour_complete"}
        or all(quest_id in available_ids for quest_id in item.quest_ids)
    ]
