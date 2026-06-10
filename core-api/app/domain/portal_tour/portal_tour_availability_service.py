# app/domain/portal_tour/portal_tour_availability_service.py

from dataclasses import dataclass

from app.domain.portal_tour.portal_tour_quest_catalog import (
    CURRENT_PORTAL_TOUR_VERSION,
    PortalTourQuestDefinition,
    get_portal_tour_quest_catalog,
)


@dataclass(frozen=True)
class PortalTourUserContext:
    permissions: frozenset[str]
    is_superadmin: bool


def user_has_permission(
    context: PortalTourUserContext,
    permission_code: str,
) -> bool:
    if context.is_superadmin:
        return True
    return permission_code in context.permissions


def is_quest_available_to_user(
    quest: PortalTourQuestDefinition,
    context: PortalTourUserContext,
) -> bool:
    if not quest.required_permissions:
        return True
    return all(user_has_permission(context, code) for code in quest.required_permissions)


def resolve_available_quests(
    context: PortalTourUserContext,
) -> list[PortalTourQuestDefinition]:
    return [
        quest
        for quest in get_portal_tour_quest_catalog()
        if is_quest_available_to_user(quest, context)
    ]


def resolve_required_quest_ids(
    available_quests: list[PortalTourQuestDefinition],
) -> list[str]:
    return [quest.id for quest in available_quests if not quest.optional]


def resolve_optional_quest_ids(
    available_quests: list[PortalTourQuestDefinition],
) -> list[str]:
    return [quest.id for quest in available_quests if quest.optional]


def resolve_new_quest_ids(
    available_quests: list[PortalTourQuestDefinition],
    completed_quest_ids: set[str],
    *,
    tour_version: str = CURRENT_PORTAL_TOUR_VERSION,
) -> list[str]:
    """Desafios novos na versão atual que o usuário ainda não concluiu."""
    version = (tour_version or "").strip() or CURRENT_PORTAL_TOUR_VERSION
    return [
        quest.id
        for quest in available_quests
        if quest.introduced_in_version == version and quest.id not in completed_quest_ids
    ]


def quests_by_category(
    available_quests: list[PortalTourQuestDefinition],
) -> dict[str, list[PortalTourQuestDefinition]]:
    grouped: dict[str, list[PortalTourQuestDefinition]] = {}
    for quest in available_quests:
        grouped.setdefault(quest.category, []).append(quest)
    return grouped
