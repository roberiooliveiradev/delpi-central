# app/domain/ports/notification_dispatch_repository.py

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol, Tuple, List
from uuid import UUID


NotificationDispatchStatus = Literal["pending", "processing", "completed", "failed"]


@dataclass
class NotificationDispatchDTO:
    id: UUID | None
    created_by_user_id: str | None
    status: NotificationDispatchStatus
    scheduled_at: datetime | None
    processed_at: datetime | None
    broadcast: bool
    recipient_count: int
    created_count: int
    title: str | None
    category: str
    presentation: str
    template_id: str | None
    source_app: str | None
    payload: dict
    notification_ids: list[str] | None
    error_message: str | None
    created_at: datetime | None = None


class NotificationDispatchRepository(Protocol):

    def create(self, dispatch: NotificationDispatchDTO) -> UUID:
        ...

    def get(self, dispatch_id: UUID) -> NotificationDispatchDTO | None:
        ...

    def update(self, dispatch: NotificationDispatchDTO) -> None:
        ...

    def delete(self, dispatch_id: UUID) -> None:
        ...

    def list_recent(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[NotificationDispatchDTO], int]:
        ...

    def list_due_pending(self, *, limit: int = 20) -> List[NotificationDispatchDTO]:
        ...
