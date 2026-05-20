# app/application/use_cases/list_notification_dispatches_use_case.py

from dataclasses import dataclass
from typing import List

from app.application.dto.list_notification_dispatches_filters import (
    ListNotificationDispatchesFilters,
)
from app.application.unit_of_work import UnitOfWork
from app.domain.ports.notification_dispatch_repository import NotificationDispatchDTO


@dataclass
class ListNotificationDispatchesResult:
    items: List[NotificationDispatchDTO]
    total: int
    limit: int
    offset: int


class ListNotificationDispatchesUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        filters: ListNotificationDispatchesFilters | None = None,
    ) -> ListNotificationDispatchesResult:
        safe_limit = max(1, min(limit, 100))
        safe_offset = max(0, offset)

        items, total = self.uow.notification_dispatches.list_filtered(
            limit=safe_limit,
            offset=safe_offset,
            filters=filters,
        )

        return ListNotificationDispatchesResult(
            items=items,
            total=total,
            limit=safe_limit,
            offset=safe_offset,
        )
