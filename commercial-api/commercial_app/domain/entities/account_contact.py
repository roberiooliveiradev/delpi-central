from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class AccountContact:
    id: UUID
    customer_code: str
    customer_store: str
    full_name: str
    role_title: str | None
    channel: str
    email: str | None
    phone_e164: str | None
    is_whatsapp: bool
    is_primary: bool
    source: str
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "customer_code": self.customer_code,
            "customer_store": self.customer_store,
            "full_name": self.full_name,
            "role_title": self.role_title,
            "channel": self.channel,
            "email": self.email,
            "phone_e164": self.phone_e164,
            "is_whatsapp": self.is_whatsapp,
            "is_primary": self.is_primary,
            "source": self.source,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
