from dataclasses import dataclass


@dataclass(frozen=True)
class UpdateChatProjectRequest:
    user_id: str
    project_id: str
    name: str | None = None
    description: str | None = None
    instructions: str | None = None
    default_agent_id: str | None = None
    explicit_default_agent_id: bool = False
    visibility: str | None = None
    icon: str | None = None
    color: str | None = None
    metadata: dict | None = None
    share_conversation_context: bool | None = None
    archived: bool | None = None
