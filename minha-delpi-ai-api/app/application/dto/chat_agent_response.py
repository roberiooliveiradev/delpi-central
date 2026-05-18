from dataclasses import dataclass


@dataclass(frozen=True)
class ChatAgentResponse:
    id: str
    key: str
    name: str
    description: str | None
    enabled: bool
    metadata: dict | None
    owner_user_id: str | None
    visibility: str
    category: str | None
    icon: str | None
    response_style: str | None
    max_tool_calls: int
    requires_confirmation_for_write: bool
    access_role: str
    created_at: str
    updated_at: str
    system_prompt: str | None = None
    sessions_in_window: int | None = None
    total_sessions: int | None = None
