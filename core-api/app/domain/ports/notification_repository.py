# app/domain/ports/notification_repository.py

from typing import Protocol, List
from uuid import UUID
from dataclasses import dataclass
from uuid import UUID
from datetime import datetime


@dataclass
class NotificationDTO:
    id: UUID
    user_id: str
    title: str | None
    message: str
    type: str
    read: bool
    created_at: datetime

class NotificationRepository(Protocol):

    def create(self, notification: NotificationDTO) -> UUID:
        ...

    def list_unread(self, user_id: str) -> List[NotificationDTO]:
        ...

    def mark_read(self, notification_id: UUID) -> None:
        ...