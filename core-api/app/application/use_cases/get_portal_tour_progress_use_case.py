# app/application/use_cases/get_portal_tour_progress_use_case.py

from dataclasses import dataclass
from datetime import datetime

from app.application.unit_of_work import UnitOfWork
from app.domain.portal_tour.portal_tour_quest_catalog import CURRENT_PORTAL_TOUR_VERSION


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

        status = progress.status
        if status in {"dismissed", "completed"} and not progress.completed_quest_ids:
            progress = self.uow.portal_tour.upsert_progress(
                user_id=user_id,
                tour_version=progress.tour_version,
                status="exploring",
                completed_quest_ids=list(progress.completed_quest_ids),
                completed_at=None,
            )
            status = progress.status
        elif status == "dismissed":
            progress = self.uow.portal_tour.upsert_progress(
                user_id=user_id,
                tour_version=progress.tour_version,
                status="exploring",
                completed_quest_ids=list(progress.completed_quest_ids),
                completed_at=progress.completed_at,
            )
            status = progress.status

        completed_quest_ids = list(progress.completed_quest_ids)
        quest_events = self.uow.portal_tour.list_quest_events(
            user_id,
            tour_version=progress.tour_version or CURRENT_PORTAL_TOUR_VERSION,
        )
        seen = set(completed_quest_ids)
        for event in quest_events:
            if event.quest_id in seen:
                continue
            completed_quest_ids.append(event.quest_id)
            seen.add(event.quest_id)

        return PortalTourProgressResult(
            tour_version=progress.tour_version,
            status=status,
            completed_quest_ids=completed_quest_ids,
            started_at=progress.started_at,
            last_activity_at=progress.last_activity_at,
            completed_at=progress.completed_at,
        )
