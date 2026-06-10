# app/application/use_cases/get_portal_tour_insights_use_case.py

from dataclasses import dataclass
from datetime import datetime

from app.application.unit_of_work import UnitOfWork
from app.domain.portal_tour.portal_tour_quest_catalog import (
    CURRENT_PORTAL_TOUR_VERSION,
)
from app.domain.portal_tour.portal_tour_insights_service import (
    compute_exploration_duration_seconds,
    compute_return_streak,
)


@dataclass
class PortalTourInsightsResult:
    exploration_duration_seconds: int | None
    quests_completed_after_return: int
    return_streak_message: str | None


class GetPortalTourInsightsUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(
        self,
        user_id: str,
        *,
        tour_version: str | None = None,
    ) -> PortalTourInsightsResult:
        version = (tour_version or "").strip() or CURRENT_PORTAL_TOUR_VERSION
        progress = self.uow.portal_tour.get_progress(user_id)
        quest_events = self.uow.portal_tour.list_quest_events(
            user_id,
            tour_version=version,
        )

        duration = compute_exploration_duration_seconds(progress)
        quests_after_return, streak_message = compute_return_streak(quest_events)

        if progress and progress.status != "exploring":
            streak_message = None
            quests_after_return = 0

        return PortalTourInsightsResult(
            exploration_duration_seconds=duration,
            quests_completed_after_return=quests_after_return,
            return_streak_message=streak_message,
        )
