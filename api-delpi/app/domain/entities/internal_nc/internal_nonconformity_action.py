# app/domain/entities/internal_nc/internal_nonconformity_action.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass(slots=True)
class InternalNonconformityAction:
    id: str
    nonconformity_id: str
    root_cause_id: Optional[str]
    action_type: str
    title: str
    description: str
    responsible_user_id: Optional[str]
    responsible_external_name: Optional[str]
    responsible_external_email: Optional[str]
    start_date: Optional[date]
    due_date: date
    completed_at: Optional[datetime]
    status: str
    verification_required: bool
    effectiveness_due_date: Optional[date]
    completion_notes: Optional[str]
    created_by_user_id: str
    created_at: datetime
    updated_at: datetime