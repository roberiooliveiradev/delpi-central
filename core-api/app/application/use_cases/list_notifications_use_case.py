# app/application/use_cases/list_notifications_use_case.py

from dataclasses import dataclass
from typing import List, Literal

from app.application.unit_of_work import UnitOfWork
from app.domain.ports.notification_repository import NotificationDTO

NotificationListStatus = Literal["all", "unread", "read"]


@dataclass
class ListNotificationsResult:
    items: List[NotificationDTO]
    total: int
    limit: int
    offset: int


class ListNotificationsUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(
        self,
        user_id: str,
        *,
        status: NotificationListStatus = "all",
        limit: int = 20,
        offset: int = 0,
    ) -> ListNotificationsResult:
        safe_limit = max(1, min(limit, 100))
        safe_offset = max(0, offset)

        items, total = self.uow.notifications.list_for_user(
            user_id,
            status=status,
            limit=safe_limit,
            offset=safe_offset,
        )

        return ListNotificationsResult(
            items=items,
            total=total,
            limit=safe_limit,
            offset=safe_offset,
        )
