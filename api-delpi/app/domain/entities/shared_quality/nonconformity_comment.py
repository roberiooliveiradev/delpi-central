# app/domain/entities/shared_quality/nonconformity_comment.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class NonconformityComment:
    id: str
    nc_type: str
    nc_id: str
    comment_type: str
    content: str
    is_internal: bool
    created_by_user_id: str
    created_at: datetime