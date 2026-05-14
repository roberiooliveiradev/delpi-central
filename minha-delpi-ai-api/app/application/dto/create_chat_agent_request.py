from dataclasses import dataclass


@dataclass(frozen=True)
class CreateChatAgentRequest:
    user_id: str
    key: str | None
    name: str
    description: str | None = None
    system_prompt: str | None = None
    visibility: str = "private"
    category: str | None = None
    icon: str | None = None
    response_style: str | None = None
    metadata: dict | None = None
    can_manage_official_agents: bool = False
