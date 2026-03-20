# app/domain/entities/external_nc/external_nonconformity_effectiveness_check.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class ExternalNonconformityEffectivenessCheck:
    id: str
    nonconformity_id: str
    action_id: Optional[str]
    checked_by_user_id: str
    checked_at: datetime
    criteria: str
    result: str
    notes: Optional[str]
    next_action: Optional[str]
    created_at: datetime