from dataclasses import dataclass


@dataclass(frozen=True)
class ChatProjectResponse:
    id: str
    name: str
    description: str | None
    created_at: str
    updated_at: str
    instructions: str | None
    default_agent_id: str | None
    visibility: str
    icon: str | None
    color: str | None
    archived_at: str | None
    metadata: dict | None
    access_role: str
    share_conversation_context: bool = False
