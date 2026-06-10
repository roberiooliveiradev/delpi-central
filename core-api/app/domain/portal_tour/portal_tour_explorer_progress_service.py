# app/domain/portal_tour/portal_tour_explorer_progress_service.py

from dataclasses import dataclass

from app.domain.portal_tour.portal_tour_availability_service import (
    PortalTourUserContext,
    resolve_available_quests,
    resolve_required_quest_ids,
)
from app.domain.portal_tour.portal_tour_gamification_service import (
    compute_progress_percent,
    resolve_explorer_level,
)


@dataclass(frozen=True)
class PortalTourExplorerProgressSnapshot:
    progress_percent: int
    explorer_level: str
    required_quest_total: int
    required_quest_done: int


def resolve_explorer_progress_snapshot(
    completed_quest_ids: list[str],
    context: PortalTourUserContext,
) -> PortalTourExplorerProgressSnapshot:
    available = resolve_available_quests(context)
    required_ids = resolve_required_quest_ids(available)
    completed = set(completed_quest_ids or [])
    done = sum(1 for quest_id in required_ids if quest_id in completed)
    progress_percent = compute_progress_percent(completed, required_ids)
    return PortalTourExplorerProgressSnapshot(
        progress_percent=progress_percent,
        explorer_level=resolve_explorer_level(progress_percent),
        required_quest_total=len(required_ids),
        required_quest_done=done,
    )
