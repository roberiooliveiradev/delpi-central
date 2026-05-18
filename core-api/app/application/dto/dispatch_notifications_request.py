from dataclasses import dataclass


ALLOWED_NOTIFICATION_TYPES = frozenset({"info", "success", "warning", "error"})


@dataclass(frozen=True)
class DispatchNotificationsRequest:
    title: str | None
    message: str
    type: str
    broadcast: bool
    user_ids: list[str]
    emails: list[str]
    source_app: str | None = None
