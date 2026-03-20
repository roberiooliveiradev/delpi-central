# app/application/dto/external_nc/add_external_nc_root_cause_request.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class AddExternalNcRootCauseRequest:
    nonconformity_id: str
    analysis_method: Optional[str]
    cause_dimension: Optional[str]
    category: Optional[str]
    why_level: Optional[int]
    description: str
    is_root_cause: bool
    created_by_user_id: str