# app/infrastructure/persistence/sqlalchemy/notification_repository.py

import uuid
from datetime import datetime
from typing import List
from uuid import UUID
from sqlalchemy.orm import Session

from app.domain.ports.notification_repository import (
    NotificationRepository,
    NotificationData,
)
from app.infrastructure.db.models import Notification


class SqlAlchemyNotificationRepository(NotificationRepository):

    def __init__(self, session: Session):
        self.session = session

    def create(self, notification: NotificationData) -> UUID:
        model = Notification(
            id=uuid.uuid4(),
            user_id=notification.user_id,
            title=notification.title,
            message=notification.message,
            type=notification.type,
        )

        self.session.add(model)
        return model.id

    def list_unread(self, user_id: str) -> List[NotificationData]:
        rows = (
            self.session.query(Notification)
            .filter_by(user_id=user_id, read_at=None)
            .order_by(Notification.created_at.desc())
            .all()
        )

        return [
            NotificationData(
                user_id=row.user_id,
                title=row.title,
                message=row.message,
                type=row.type,
            )
            for row in rows
        ]

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