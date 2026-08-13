from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class CommercialUserProfile:
    user_id: str
    job_title: str | None
    photo_storage_key: str | None
    photo_file_name: str | None
    photo_content_type: str | None
    photo_byte_size: int | None
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "job_title": self.job_title,
            "has_photo": bool(self.photo_storage_key),
            "photo_url": (
                f"/users/{self.user_id}/profile/photo" if self.photo_storage_key else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
