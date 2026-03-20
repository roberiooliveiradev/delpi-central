# app/application/dto/external_nc/remove_external_nc_team_member_request.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RemoveExternalNcTeamMemberRequest:
    nonconformity_id: str
    member_id: str
    actor_user_id: str