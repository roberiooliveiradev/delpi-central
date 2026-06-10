# app/infrastructure/persistence/sqlalchemy/portal_tour_repository.py

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.ports.portal_tour_repository import (
    PortalTourExplorerDTO,
    PortalTourProgressDTO,
    PortalTourQuestEventDTO,
    PortalTourTopExplorerDTO,
    PortalTourRepository,
)
from app.infrastructure.db.models.user import User
from app.infrastructure.db.models.user_portal_tour_progress import (
    PortalTourQuestEvent,
    UserPortalTourProgress,
)


def _normalize_quest_ids(quest_ids: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for quest_id in quest_ids:
        value = (quest_id or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        normalized.append(value)
    return normalized


def _to_progress_dto(row: UserPortalTourProgress) -> PortalTourProgressDTO:
    return PortalTourProgressDTO(
        user_id=str(row.user_id),
        tour_version=row.tour_version,
        status=row.status,
        completed_quest_ids=list(row.completed_quest_ids or []),
        started_at=row.started_at,
        last_activity_at=row.last_activity_at,
        completed_at=row.completed_at,
    )


class SqlAlchemyPortalTourRepository(PortalTourRepository):

    def __init__(self, session: Session):
        self.session = session

    def get_progress(self, user_id: str) -> PortalTourProgressDTO | None:
        row = self.session.get(UserPortalTourProgress, UUID(user_id))
        if not row:
            return None
        return _to_progress_dto(row)

    def upsert_progress(
        self,
        *,
        user_id: str,
        tour_version: str,
        status: str,
        completed_quest_ids: list[str],
        completed_at: datetime | None = None,
    ) -> PortalTourProgressDTO:
        now = datetime.utcnow()
        normalized_quest_ids = _normalize_quest_ids(completed_quest_ids)
        uid = UUID(user_id)
        row = self.session.get(UserPortalTourProgress, uid)

        if row:
            if row.tour_version != tour_version:
                row.tour_version = tour_version
                row.started_at = now
                row.completed_at = None
            row.status = status
            row.completed_quest_ids = normalized_quest_ids
            row.last_activity_at = now
            row.updated_at = now
            row.completed_at = completed_at
            return _to_progress_dto(row)

        row = UserPortalTourProgress(
            user_id=uid,
            tour_version=tour_version,
            status=status,
            completed_quest_ids=normalized_quest_ids,
            started_at=now,
            last_activity_at=now,
            completed_at=completed_at,
            updated_at=now,
        )
        self.session.add(row)
        return _to_progress_dto(row)

    def record_quest_completion(
        self,
        *,
        user_id: str,
        tour_version: str,
        quest_id: str,
        completed_at: datetime | None = None,
    ) -> bool:
        normalized_quest_id = (quest_id or "").strip()
        if not normalized_quest_id:
            return False

        uid = UUID(user_id)
        when = completed_at or datetime.utcnow()
        existing = (
            self.session.query(PortalTourQuestEvent)
            .filter_by(
                user_id=uid,
                tour_version=tour_version,
                quest_id=normalized_quest_id,
            )
            .first()
        )
        if existing:
            return False

        self.session.add(
            PortalTourQuestEvent(
                user_id=uid,
                tour_version=tour_version,
                quest_id=normalized_quest_id,
                completed_at=when,
            )
        )
        return True

    def delete_progress(self, user_id: str) -> None:
        uid = UUID(user_id)
        self.session.query(PortalTourQuestEvent).filter_by(user_id=uid).delete()
        row = self.session.get(UserPortalTourProgress, uid)
        if row:
            self.session.delete(row)

    def list_explorers(
        self,
        *,
        tour_version: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[PortalTourExplorerDTO], int]:
        query = (
            self.session.query(UserPortalTourProgress, User)
            .join(User, User.id == UserPortalTourProgress.user_id)
            .order_by(UserPortalTourProgress.last_activity_at.desc())
        )

        if tour_version:
            query = query.filter(UserPortalTourProgress.tour_version == tour_version)
        if status:
            query = query.filter(UserPortalTourProgress.status == status)

        total = query.count()
        rows = query.offset(max(offset, 0)).limit(min(max(limit, 1), 200)).all()

        items = [
            PortalTourExplorerDTO(
                user_id=str(progress.user_id),
                name=user.name,
                email=user.email,
                tour_version=progress.tour_version,
                status=progress.status,
                completed_quest_ids=list(progress.completed_quest_ids or []),
                completed_quest_count=len(progress.completed_quest_ids or []),
                started_at=progress.started_at,
                last_activity_at=progress.last_activity_at,
                completed_at=progress.completed_at,
            )
            for progress, user in rows
        ]
        return items, total

    def list_quest_events(
        self,
        user_id: str,
        *,
        tour_version: str | None = None,
    ) -> list[PortalTourQuestEventDTO]:
        uid = UUID(user_id)
        query = (
            self.session.query(PortalTourQuestEvent)
            .filter_by(user_id=uid)
            .order_by(PortalTourQuestEvent.completed_at.asc())
        )
        if tour_version:
            query = query.filter_by(tour_version=tour_version)

        return [
            PortalTourQuestEventDTO(
                quest_id=row.quest_id,
                tour_version=row.tour_version,
                completed_at=row.completed_at,
            )
            for row in query.all()
        ]

    def list_top_explorers(
        self,
        *,
        tour_version: str | None = None,
        period_days: int = 7,
        limit: int = 10,
    ) -> list[PortalTourTopExplorerDTO]:
        since = datetime.utcnow() - timedelta(days=period_days)

        query = (
            self.session.query(
                PortalTourQuestEvent.user_id,
                PortalTourQuestEvent.tour_version,
                func.count(PortalTourQuestEvent.id).label("quests_in_period"),
                func.max(PortalTourQuestEvent.completed_at).label("last_activity_at"),
                User.name,
                User.email,
            )
            .join(User, User.id == PortalTourQuestEvent.user_id)
            .filter(PortalTourQuestEvent.completed_at >= since)
            .group_by(
                PortalTourQuestEvent.user_id,
                PortalTourQuestEvent.tour_version,
                User.name,
                User.email,
            )
            .order_by(func.count(PortalTourQuestEvent.id).desc())
            .limit(limit)
        )

        if tour_version:
            query = query.filter(PortalTourQuestEvent.tour_version == tour_version)

        return [
            PortalTourTopExplorerDTO(
                user_id=str(row.user_id),
                name=row.name,
                email=row.email,
                tour_version=row.tour_version,
                quests_in_period=int(row.quests_in_period),
                last_activity_at=row.last_activity_at,
            )
            for row in query.all()
        ]
