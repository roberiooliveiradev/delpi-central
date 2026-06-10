# app/application/use_cases/get_portal_tour_achievements_use_case.py

from dataclasses import dataclass
from datetime import datetime

from app.application.unit_of_work import UnitOfWork
from app.domain.portal_tour.portal_tour_achievement_catalog import (
    PortalTourAchievementDefinition,
    get_portal_tour_achievement_catalog,
)
from app.domain.portal_tour.portal_tour_availability_service import (
    PortalTourUserContext,
    resolve_available_quests,
    resolve_required_quest_ids,
)
from app.domain.portal_tour.portal_tour_gamification_service import (
    compute_progress_percent,
    resolve_explorer_level,
)
from app.domain.portal_tour.portal_tour_quest_catalog import CURRENT_PORTAL_TOUR_VERSION


@dataclass
class PortalTourAchievementItem:
    id: str
    title: str
    description: str
    kind: str
    unlocked: bool
    unlocked_at: datetime | None


@dataclass
class PortalTourAchievementsResult:
    tour_version: str
    unlocked_count: int
    total_count: int
    progress_percent: int
    explorer_level: str
    items: list[PortalTourAchievementItem]


def _is_achievement_unlocked(
    definition: PortalTourAchievementDefinition,
    *,
    completed_quest_ids: set[str],
    progress_percent: int,
    tour_status: str | None,
) -> bool:
    if definition.kind in {"category", "quest"}:
        return all(quest_id in completed_quest_ids for quest_id in definition.quest_ids)

    if definition.kind == "milestone":
        return progress_percent >= (definition.milestone_percent or 0)

    if definition.kind == "tour_complete":
        return tour_status == "completed" or progress_percent >= 100

    return False


def _resolve_unlocked_at(
    definition: PortalTourAchievementDefinition,
    *,
    completed_quest_ids: set[str],
    quest_completed_at: dict[str, datetime],
    progress_completed_at: datetime | None,
) -> datetime | None:
    if definition.kind in {"category", "quest"}:
        timestamps = [
            quest_completed_at[quest_id]
            for quest_id in definition.quest_ids
            if quest_id in quest_completed_at
        ]
        return max(timestamps) if timestamps else None

    if definition.kind == "tour_complete":
        return progress_completed_at

    return None


class GetPortalTourAchievementsUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(
        self,
        user_id: str,
        context: PortalTourUserContext,
        *,
        tour_version: str | None = None,
    ) -> PortalTourAchievementsResult:
        version = (tour_version or "").strip() or CURRENT_PORTAL_TOUR_VERSION
        available_quests = resolve_available_quests(context)
        required_quest_ids = resolve_required_quest_ids(available_quests)
        catalog = get_portal_tour_achievement_catalog(available_quests)

        progress = self.uow.portal_tour.get_progress(user_id)
        quest_events = self.uow.portal_tour.list_quest_events(
            user_id,
            tour_version=version,
        )

        completed_quest_ids = set(progress.completed_quest_ids if progress else [])
        completed_quest_ids.update(event.quest_id for event in quest_events)

        quest_completed_at = {event.quest_id: event.completed_at for event in quest_events}

        progress_percent = compute_progress_percent(
            completed_quest_ids,
            required_quest_ids,
        )
        tour_status = progress.status if progress else None
        progress_completed_at = progress.completed_at if progress else None

        items: list[PortalTourAchievementItem] = []
        unlocked_count = 0

        for definition in catalog:
            unlocked = _is_achievement_unlocked(
                definition,
                completed_quest_ids=completed_quest_ids,
                progress_percent=progress_percent,
                tour_status=tour_status,
            )
            if unlocked:
                unlocked_count += 1

            items.append(
                PortalTourAchievementItem(
                    id=definition.id,
                    title=definition.title,
                    description=definition.description,
                    kind=definition.kind,
                    unlocked=unlocked,
                    unlocked_at=_resolve_unlocked_at(
                        definition,
                        completed_quest_ids=completed_quest_ids,
                        quest_completed_at=quest_completed_at,
                        progress_completed_at=progress_completed_at,
                    )
                    if unlocked
                    else None,
                )
            )

        return PortalTourAchievementsResult(
            tour_version=version,
            unlocked_count=unlocked_count,
            total_count=len(catalog),
            progress_percent=progress_percent,
            explorer_level=resolve_explorer_level(progress_percent),
            items=items,
        )
