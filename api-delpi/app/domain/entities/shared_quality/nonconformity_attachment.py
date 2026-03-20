# app/domain/entities/shared_quality/nonconformity_attachment.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class NonconformityAttachment:
    id: str
    nc_type: Optional[str]
    nc_id: Optional[str]
    action_id: Optional[str]
    effectiveness_check_id: Optional[str]
    file_name: str
    original_name: str
    mime_type: Optional[str]
    size_bytes: int
    storage_provider: str
    storage_path: str
    checksum: Optional[str]
    uploaded_by_user_id: str
    uploaded_at: datetime