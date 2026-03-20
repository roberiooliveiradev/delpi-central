# app/application/dto/external_nc/add_external_nc_team_member_request.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AddExternalNcTeamMemberRequest:
    nonconformity_id: str
    user_id: str
    role_in_case: str
    actor_user_id: str