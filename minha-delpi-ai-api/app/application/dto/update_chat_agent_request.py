from dataclasses import dataclass


@dataclass(frozen=True)
class UpdateChatAgentRequest:
    user_id: str
    agent_id: str
    name: str | None = None
    description: str | None = None
    system_prompt: str | None = None
    visibility: str | None = None
    category: str | None = None
    icon: str | None = None
    response_style: str | None = None
    metadata: dict | None = None
    enabled: bool | None = None
