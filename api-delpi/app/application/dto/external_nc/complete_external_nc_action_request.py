# app/application/dto/external_nc/complete_external_nc_action_request.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class CompleteExternalNcActionRequest:
    action_id: str
    actor_user_id: str
    completion_notes: Optional[str] = None