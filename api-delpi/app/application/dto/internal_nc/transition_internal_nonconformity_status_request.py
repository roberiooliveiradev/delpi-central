# app/application/dto/internal_nc/transition_internal_nonconformity_status_request.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class TransitionInternalNonconformityStatusRequest:
    nonconformity_id: str
    target_status: str
    actor_user_id: str
    justification: Optional[str] = None