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
    max_tool_calls: int | None = None
    requires_confirmation_for_write: bool | None = None
    can_manage_official_agents: bool = False
