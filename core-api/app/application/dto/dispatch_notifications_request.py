from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class DispatchNotificationsRequest:
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
    broadcast: bool
    user_ids: list[str]
    emails: list[str]
    role_ids: list[str]
    group_ids: list[str]
    excluded_user_ids: list[str] = field(default_factory=list)
    source_app: str | None = None
