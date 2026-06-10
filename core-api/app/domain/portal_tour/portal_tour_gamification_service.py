# app/domain/portal_tour/portal_tour_gamification_service.py

from app.domain.portal_tour.portal_tour_quest_catalog import PortalTourQuestDefinition


def compute_progress_percent(
    completed_quest_ids: set[str],
    required_quest_ids: list[str],
) -> int:
    if not required_quest_ids:
        return 0
    done = sum(1 for quest_id in required_quest_ids if quest_id in completed_quest_ids)
    return round((done / len(required_quest_ids)) * 100)


def resolve_explorer_level(progress_percent: int) -> str:
    if progress_percent >= 100:
        return "Mestre DELPI"
    if progress_percent >= 75:
        return "Embaixador DELPI"
    if progress_percent >= 50:
        return "Expert"
    if progress_percent >= 25:
        return "Curioso"
    return "Explorador"


def resolve_quest_xp(quest: PortalTourQuestDefinition) -> int:
    return 5 if quest.optional else 10


def compute_earned_xp(
    available_quests: list[PortalTourQuestDefinition],
    completed_quest_ids: set[str],
) -> int:
    return sum(
        resolve_quest_xp(quest)
        for quest in available_quests
        if quest.id in completed_quest_ids
    )
