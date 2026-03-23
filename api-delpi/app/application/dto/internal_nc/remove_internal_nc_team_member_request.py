from dataclasses import dataclass

@dataclass(slots=True)
class RemoveInternalNcTeamMemberRequest:
    nonconformity_id: str
    member_id: str
    actor_user_id: str