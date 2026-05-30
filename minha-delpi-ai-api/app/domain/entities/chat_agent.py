from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class ChatAgent:
    id: UUID
    name: str
    description: str | None
    system_prompt: str | None
    enabled: bool
    metadata: dict | None
    created_at: datetime
    updated_at: datetime
    owner_user_id: UUID | None = None
    visibility: str = "system"
    category: str | None = None
    icon: str | None = None
    response_style: str | None = None
    max_tool_calls: int = 5
    requires_confirmation_for_write: bool = True
    published_version: int = 0
    published_at: datetime | None = None
    published_config: dict | None = None
