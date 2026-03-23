# app/domain/entities/internal_nc/internal_nc_team_member.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class InternalNcTeamMember:
    id: str
    nonconformity_id: str
    user_id: str
    role_in_case: str
    joined_at: datetime