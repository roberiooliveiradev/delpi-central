# app/application/dto/notification_dispatch_response.py

from dataclasses import dataclass


@dataclass(frozen=True)
class NotificationDispatchResponse:
    dispatch_id: str
    status: str
    scheduled_at: str | None
    created_count: int
    notification_ids: list[str]
    recipient_count: int
    error_message: str | None = None
