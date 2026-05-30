from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class ChatProject:
    id: UUID
    user_id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    instructions: str | None = None
    default_agent_id: UUID | None = None
    visibility: str = "private"
    icon: str | None = None
    color: str | None = None
    archived_at: datetime | None = None
    metadata: dict | None = None
