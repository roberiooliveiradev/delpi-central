# app/application/use_cases/sync_portal_tour_progress_use_case.py

from dataclasses import dataclass
from datetime import datetime

from app.application.unit_of_work import UnitOfWork
from app.domain.portal_tour.portal_tour_availability_service import (
    PortalTourUserContext,
    resolve_available_quests,
    resolve_required_quest_ids,
)
from app.domain.portal_tour.portal_tour_quest_catalog import get_quest_by_id

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
        user_context: PortalTourUserContext | None = None,
    ) -> SyncPortalTourProgressResult:
        version = (tour_version or "").strip()
        if not version:
            raise ValueError("tourVersion is required")

        normalized_status = (status or "").strip().lower()
        if normalized_status == "dismissed":
            normalized_status = "exploring"
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

        if user_context is not None:
            merged_quest_ids = self._filter_available_quest_ids(
                merged_quest_ids,
                user_context,
            )

        if normalized_status == "completed":
            if not self._can_mark_completed(merged_quest_ids, user_context):
                normalized_status = "exploring"

        if normalized_status == "completed":
            completed_at = datetime.utcnow()
        else:
            completed_at = None if normalized_status == "exploring" else (
                existing.completed_at if existing else None
            )

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

    @staticmethod
    def _can_mark_completed(
        merged_quest_ids: list[str],
        user_context: PortalTourUserContext | None,
    ) -> bool:
        if not merged_quest_ids:
            return False
        if user_context is None:
            return True
        available = resolve_available_quests(user_context)
        required_ids = resolve_required_quest_ids(available)
        if not required_ids:
            return False
        completed = set(merged_quest_ids)
        return all(quest_id in completed for quest_id in required_ids)

    @staticmethod
    def _filter_available_quest_ids(
        quest_ids: list[str],
        context: PortalTourUserContext,
    ) -> list[str]:
        available_ids = {quest.id for quest in resolve_available_quests(context)}
        filtered: list[str] = []
        for quest_id in quest_ids:
            if quest_id not in available_ids:
                continue
            if get_quest_by_id(quest_id) is None:
                continue
            filtered.append(quest_id)
        return filtered
