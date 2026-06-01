from dataclasses import dataclass


@dataclass(frozen=True)
class CreateChatProjectRequest:
    user_id: str
    name: str
    description: str | None = None
    instructions: str | None = None
    default_agent_id: str | None = None
    visibility: str = "private"
    icon: str | None = None
    color: str | None = None
    metadata: dict | None = None
    share_conversation_context: bool | None = None
