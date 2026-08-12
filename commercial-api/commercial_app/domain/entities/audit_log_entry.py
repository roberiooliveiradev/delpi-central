from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class AuditLogEntry:
    id: str
    actor_user_id: str
    action: str
    entity_type: str
    entity_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None


@dataclass(frozen=True)
class AuditLogPage:
    items: tuple[AuditLogEntry, ...]
    total: int
    page: int
    page_size: int
