# app/application/dto/external_nc/update_external_nc_action_request.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(slots=True)
class UpdateExternalNcActionRequest:
    action_id: str
    root_cause_id: Optional[str]
    action_type: str
    title: str
    description: str
    responsible_user_id: Optional[str]
    responsible_external_name: Optional[str]
    responsible_external_email: Optional[str]
    start_date: Optional[date]
    due_date: date
    verification_required: bool
    effectiveness_due_date: Optional[date]