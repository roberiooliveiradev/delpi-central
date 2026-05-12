from dataclasses import dataclass


@dataclass(frozen=True)
class ShareChatAgentRequest:
    user_id: str
    agent_id: str
    target_user_id: str
    role: str = "viewer"
