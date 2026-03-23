# app/application/dto/internal_nc/register_internal_nc_effectiveness_check_request.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class RegisterInternalNcEffectivenessCheckRequest:
    nonconformity_id: str
    action_id: Optional[str]
    checked_by_user_id: str
    checked_at: datetime
    criteria: str
    result: str
    notes: Optional[str] = None
    next_action: Optional[str] = None