from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ProcessDocument:
    id: str
    processo_id: str
    title: str
    content_md: str
    created_by_user_id: str
    updated_by_user_id: str
    created_at: datetime | None
    updated_at: datetime | None
    deleted_at: datetime | None = None

    def to_summary_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "processo_id": self.processo_id,
            "title": self.title,
            "created_by_user_id": self.created_by_user_id,
            "updated_by_user_id": self.updated_by_user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self.to_summary_dict()
        payload["content_md"] = self.content_md
        return payload
