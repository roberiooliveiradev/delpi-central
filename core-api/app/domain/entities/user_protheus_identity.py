from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


MAPPING_STATUSES = frozenset({"mapped", "unmapped", "ambiguous"})
MAPPING_SOURCES = frozenset({"manual", "email_match", "login_match"})


@dataclass(frozen=True)
class UserProtheusIdentity:
    user_id: UUID
    protheus_user_id: str | None
    protheus_user_code: str | None
    mapping_status: str
    mapping_source: str | None
    verified: bool
    updated_by_user_id: UUID | None
    created_at: datetime | None
    updated_at: datetime | None

    def to_dict(self) -> dict:
        return {
            "user_id": str(self.user_id),
            "protheus_user_id": self.protheus_user_id,
            "protheus_user_code": self.protheus_user_code,
            "mapping_status": self.mapping_status,
            "mapping_source": self.mapping_source,
            "verified": bool(self.verified),
            "updated_by_user_id": (
                str(self.updated_by_user_id) if self.updated_by_user_id else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
