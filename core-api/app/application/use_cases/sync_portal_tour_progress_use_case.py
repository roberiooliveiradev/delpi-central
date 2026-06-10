# app/application/use_cases/sync_portal_tour_progress_use_case.py

from dataclasses import dataclass
from datetime import datetime

from app.application.unit_of_work import UnitOfWork

ALLOWED_STATUSES = {"exploring", "completed", "dismissed"}


@dataclass
class SyncPortalTourProgressResult:
    tour_version: str
    status: str
    completed_quest_ids: list[str]
    started_at: datetime
    last_activity_at: datetime
    completed_at: datetime | None


class SyncPortalTourProgressUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(
        self,
        user_id: str,
        *,
        tour_version: str,
        status: str,
        completed_quest_ids: list[str] | None = None,
        completed_quest_id: str | None = None,
    ) -> SyncPortalTourProgressResult:
        version = (tour_version or "").strip()
        if not version:
            raise ValueError("tourVersion is required")

        normalized_status = (status or "").strip().lower()
        if normalized_status not in ALLOWED_STATUSES:
            raise ValueError("status must be exploring, completed or dismissed")

        existing = self.uow.portal_tour.get_progress(user_id)
        merged_quest_ids = list(existing.completed_quest_ids) if existing else []

        if existing and existing.tour_version != version:
            merged_quest_ids = []

        if completed_quest_ids is not None:
            merged_quest_ids = list(completed_quest_ids)
        elif completed_quest_id:
            quest_id = completed_quest_id.strip()
            if quest_id and quest_id not in merged_quest_ids:
                merged_quest_ids.append(quest_id)

        if normalized_status == "completed":
            completed_at = datetime.utcnow()
        else:
            completed_at = existing.completed_at if existing else None

        for quest_id in merged_quest_ids:
            self.uow.portal_tour.record_quest_completion(
                user_id=user_id,
                tour_version=version,
                quest_id=quest_id,
            )

        progress = self.uow.portal_tour.upsert_progress(
            user_id=user_id,
            tour_version=version,
            status=normalized_status,
            completed_quest_ids=merged_quest_ids,
            completed_at=completed_at,
        )

        return SyncPortalTourProgressResult(
            tour_version=progress.tour_version,
            status=progress.status,
            completed_quest_ids=list(progress.completed_quest_ids),
            started_at=progress.started_at,
            last_activity_at=progress.last_activity_at,
            completed_at=progress.completed_at,
        )
