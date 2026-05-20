# app/infrastructure/persistence/sqlalchemy/notification_repository.py

import uuid
from datetime import date, datetime, time
from typing import List, Literal, Tuple
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.domain.notifications.notification_constants import ALLOWED_NOTIFICATION_CATEGORIES
from app.domain.ports.notification_repository import (
    NotificationRepository,
    NotificationDTO,
)
from app.infrastructure.db.models import Notification


class SqlAlchemyNotificationRepository(NotificationRepository):

    def __init__(self, session: Session):
        self.session = session

    def create(self, notification: NotificationDTO) -> UUID:
        model = Notification(
            id=uuid.uuid4(),
            user_id=notification.user_id,
            title=notification.title,
            message=notification.message,
            type=notification.type,
            category=notification.category,
            presentation=notification.presentation,
            html_content=notification.html_content,
            action_type=notification.action_type,
            action_label=notification.action_label,
            action_target=notification.action_target,
            icon=notification.icon,
            notification_metadata=notification.metadata,
            expires_at=notification.expires_at,
        )

        self.session.add(model)
        return model.id

    def get(self, notification_id: UUID) -> NotificationDTO | None:
        row = self.session.get(Notification, notification_id)
        if not row or row.deleted_at is not None:
            return None

        return self._to_dto(row)

    def list_by_ids(self, notification_ids: List[UUID]) -> List[NotificationDTO]:
        if not notification_ids:
            return []

        rows = (
            self.session.query(Notification)
            .filter(
                Notification.id.in_(notification_ids),
                Notification.deleted_at.is_(None),
            )
            .all()
        )
        return [self._to_dto(row) for row in rows]

    def list_unread(self, user_id: str) -> List[NotificationDTO]:
        items, _total = self.list_for_user(
            user_id,
            status="unread",
            limit=500,
            offset=0,
        )
        return items

    def list_for_user(
        self,
        user_id: str,
        *,
        status: Literal["all", "unread", "read"] = "all",
        category: str | None = None,
        important_only: bool = False,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[NotificationDTO], int]:
        now = datetime.utcnow()

        query = self.session.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.deleted_at.is_(None),
            or_(Notification.expires_at.is_(None), Notification.expires_at > now),
        )

        if status == "unread":
            query = query.filter(Notification.read_at.is_(None))
        elif status == "read":
            query = query.filter(Notification.read_at.isnot(None))

        if category:
            normalized = category.strip().lower()
            if normalized in ALLOWED_NOTIFICATION_CATEGORIES:
                query = query.filter(Notification.category == normalized)

        if important_only:
            query = query.filter(Notification.is_important.is_(True))

        total = query.count()

        rows = (
            query.order_by(
                Notification.is_important.desc(),
                Notification.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
            .all()
        )

        return [self._to_dto(row) for row in rows], total

    def soft_delete(self, notification_id: UUID) -> None:
        row = self.session.get(Notification, notification_id)
        if row and row.deleted_at is None:
            row.deleted_at = datetime.utcnow()

    def soft_delete_many(self, notification_ids: List[UUID]) -> int:
        if not notification_ids:
            return 0

        now = datetime.utcnow()
        updated = (
            self.session.query(Notification)
            .filter(
                Notification.id.in_(notification_ids),
                Notification.deleted_at.is_(None),
            )
            .update({"deleted_at": now}, synchronize_session=False)
        )
        return int(updated)

    def set_important(self, notification_id: UUID, *, is_important: bool) -> None:
        row = self.session.get(Notification, notification_id)
        if row and row.deleted_at is None:
            row.is_important = is_important

    def mark_read(self, notification_id: UUID) -> None:
        row = self.session.get(Notification, notification_id)
        if row:
            row.read_at = datetime.utcnow()

    def mark_all_read(self, user_id: str) -> None:
        (
            self.session.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.read_at.is_(None),
                Notification.deleted_at.is_(None),
            )
            .update({"read_at": datetime.utcnow()}, synchronize_session=False)
        )

    def has_category_notification_on_date(
        self,
        user_id: str,
        category: str,
        on_date: date,
    ) -> bool:
        day_start = datetime.combine(on_date, time.min)
        day_end = datetime.combine(on_date, time.max)
        row = (
            self.session.query(Notification.id)
            .filter(
                Notification.user_id == UUID(user_id),
                Notification.category == category,
                Notification.deleted_at.is_(None),
                Notification.created_at >= day_start,
                Notification.created_at <= day_end,
            )
            .first()
        )
        return row is not None

    @staticmethod
    def _to_dto(row: Notification) -> NotificationDTO:
        return NotificationDTO(
            id=row.id,
            user_id=str(row.user_id),
            title=row.title,
            message=row.message,
            type=row.type,
            category=getattr(row, "category", None) or "system",
            presentation=getattr(row, "presentation", None) or "text",
            html_content=getattr(row, "html_content", None),
            action_type=getattr(row, "action_type", None),
            action_label=getattr(row, "action_label", None),
            action_target=getattr(row, "action_target", None),
            icon=getattr(row, "icon", None),
            metadata=getattr(row, "notification_metadata", None),
            expires_at=getattr(row, "expires_at", None),
            is_important=bool(getattr(row, "is_important", False)),
            read=row.read_at is not None,
            created_at=row.created_at,
        )
