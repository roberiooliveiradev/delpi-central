# app/domain/ports/notification_repository.py

from typing import Protocol, List
from uuid import UUID
from dataclasses import dataclass


@dataclass
class NotificationData:
    user_id: str
    title: str | None
    message: str
    type: str

class NotificationRepository(Protocol):

    def create(self, notification: NotificationData) -> UUID:
        ...

    def list_unread(self, user_id: str) -> List[NotificationData]:
        ...

    def mark_read(self, notification_id: UUID) -> None:
        ...