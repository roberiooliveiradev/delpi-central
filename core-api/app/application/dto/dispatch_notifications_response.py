from dataclasses import dataclass


@dataclass(frozen=True)
class DispatchNotificationsResponse:
    created_count: int
    notification_ids: list[str]
