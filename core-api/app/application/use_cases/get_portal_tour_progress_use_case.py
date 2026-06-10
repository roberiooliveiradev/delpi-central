# app/application/use_cases/get_portal_tour_progress_use_case.py

from dataclasses import dataclass
from datetime import datetime

from app.application.unit_of_work import UnitOfWork


@dataclass
class PortalTourProgressResult:
    tour_version: str | None
    status: str | None
    completed_quest_ids: list[str]
    started_at: datetime | None
    last_activity_at: datetime | None
    completed_at: datetime | None


class GetPortalTourProgressUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, user_id: str) -> PortalTourProgressResult:
        progress = self.uow.portal_tour.get_progress(user_id)
        if not progress:
            return PortalTourProgressResult(
                tour_version=None,
                status=None,
                completed_quest_ids=[],
                started_at=None,
                last_activity_at=None,
                completed_at=None,
            )

        return PortalTourProgressResult(
            tour_version=progress.tour_version,
            status=progress.status,
            completed_quest_ids=list(progress.completed_quest_ids),
            started_at=progress.started_at,
            last_activity_at=progress.last_activity_at,
            completed_at=progress.completed_at,
        )
