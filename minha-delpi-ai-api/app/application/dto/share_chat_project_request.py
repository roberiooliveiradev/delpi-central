from dataclasses import dataclass


@dataclass(frozen=True)
class ShareChatProjectRequest:
    user_id: str
    project_id: str
    target_user_id: str
    role: str = "viewer"
