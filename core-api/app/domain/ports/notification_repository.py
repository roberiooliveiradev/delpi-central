# app/domain/ports/notification_repository.py

from typing import Protocol, List, Tuple, Literal
from uuid import UUID
from dataclasses import dataclass
from datetime import date, datetime


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
    is_important: bool = False
    id: UUID | None = None
    created_at: datetime | None = None


class NotificationRepository(Protocol):

    def create(self, notification: NotificationDTO) -> UUID:
        ...

    def get(self, notification_id: UUID) -> NotificationDTO | None:
        ...

    def list_unread(self, user_id: str) -> List[NotificationDTO]:
        ...

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
        ...

    def soft_delete(self, notification_id: UUID) -> None:
        ...

    def set_important(self, notification_id: UUID, *, is_important: bool) -> None:
        ...

    def mark_read(self, notification_id: UUID) -> None:
        ...

    def mark_all_read(self, user_id: str) -> None:
        ...

    def has_category_notification_on_date(
        self,
        user_id: str,
        category: str,
        on_date: date,
    ) -> bool:
        ...
