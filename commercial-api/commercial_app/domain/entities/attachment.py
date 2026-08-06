from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class CommercialAttachment:
    id: UUID
    owner_type: str
    owner_id: str
    file_name: str
    storage_key: str
    content_type: str
    byte_size: int
    uploaded_by_user_id: str
    created_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "owner_type": self.owner_type,
            "owner_id": self.owner_id,
            "file_name": self.file_name,
            "storage_key": self.storage_key,
            "content_type": self.content_type,
            "byte_size": self.byte_size,
            "uploaded_by_user_id": self.uploaded_by_user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
