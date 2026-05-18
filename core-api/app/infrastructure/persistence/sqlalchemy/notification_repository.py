# app/infrastructure/persistence/sqlalchemy/notification_repository.py

import uuid
from datetime import datetime
from typing import List
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

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
        if not row:
            return None

        return self._to_dto(row)

    def list_unread(self, user_id: str) -> List[NotificationDTO]:
        now = datetime.utcnow()

        rows = (
            self.session.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.read_at.is_(None),
                or_(Notification.expires_at.is_(None), Notification.expires_at > now),
            )
            .order_by(Notification.created_at.desc())
            .all()
        )

        return [self._to_dto(row) for row in rows]

    def mark_read(self, notification_id: UUID) -> None:
        row = self.session.get(Notification, notification_id)
        if row:
            row.read_at = datetime.utcnow()

    def mark_all_read(self, user_id: str) -> None:
        (
            self.session.query(Notification)
            .filter_by(user_id=user_id, read_at=None)
            .update({"read_at": datetime.utcnow()}, synchronize_session=False)
        )

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
            read=row.read_at is not None,
            created_at=row.created_at,
        )
