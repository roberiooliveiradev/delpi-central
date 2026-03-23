from dataclasses import dataclass

@dataclass(slots=True)
class AddInternalNcTeamMemberRequest:
    nonconformity_id: str
    user_id: str
    role_in_case: str
    actor_user_id: str