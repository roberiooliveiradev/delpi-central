# app/domain/entities/shared_quality/nonconformity_audit_event.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class NonconformityAuditEvent:
    id: str
    entity_type: str
    entity_id: str
    event_type: str
    actor_user_id: str | None
    payload_json: dict[str, Any] | None
    created_at: datetime