from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class PersonProfile:
    user_id: UUID
    job_title: str | None
    phone_e164: str | None
    mobile_e164: str | None
    whatsapp_e164: str | None
    photo_storage_key: str | None
    photo_file_name: str | None
    photo_content_type: str | None
    photo_byte_size: int | None
    created_at: datetime | None
    updated_at: datetime | None

    def to_api_dict(self) -> dict[str, Any]:
        has_photo = bool(self.photo_storage_key)
        return {
            "user_id": str(self.user_id),
            "job_title": self.job_title,
            "phone_e164": self.phone_e164,
            "mobile_e164": self.mobile_e164,
            "whatsapp_e164": self.whatsapp_e164,
            "has_photo": has_photo,
            "photo_url": "/me/person-profile/photo" if has_photo else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
