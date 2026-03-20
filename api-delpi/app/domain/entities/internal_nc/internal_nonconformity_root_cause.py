# app/domain/entities/internal_nc/internal_nonconformity_root_cause.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class InternalNonconformityRootCause:
    id: str
    nonconformity_id: str
    analysis_method: Optional[str]
    cause_dimension: Optional[str]
    category: Optional[str]
    why_level: Optional[int]
    description: str
    is_root_cause: bool
    created_by_user_id: str
    created_at: datetime