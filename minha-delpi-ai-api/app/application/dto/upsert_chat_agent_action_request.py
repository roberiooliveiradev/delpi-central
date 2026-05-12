from dataclasses import dataclass


@dataclass(frozen=True)
class UpsertChatAgentActionRequest:
    user_id: str
    agent_id: str
    provider_key: str
    action_id: str
    sensitivity: str = "read"
    requires_confirmation: bool = False
    enabled: bool = True
