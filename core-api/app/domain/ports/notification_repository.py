# app/domain/ports/notification_repository.py

from typing import Protocol, List
from uuid import UUID
from dataclasses import dataclass
from datetime import datetime


@dataclass
class NotificationDTO:
    user_id: str
    title: str | None
    message: str
    type: str
    category: str
    presentation: str
    html_content: str | None
    action_type: str | None
    action_label: str | None
    action_target: str | None
    icon: str | None
    metadata: dict | None
    expires_at: datetime | None
    read: bool
    id: UUID | None = None
    created_at: datetime | None = None


class NotificationRepository(Protocol):

    def create(self, notification: NotificationDTO) -> UUID:
        ...

    def get(self, notification_id: UUID) -> NotificationDTO | None:
        ...

    def list_unread(self, user_id: str) -> List[NotificationDTO]:
        ...

    def mark_read(self, notification_id: UUID) -> None:
        ...

    def mark_all_read(self, user_id: str) -> None:
        ...
