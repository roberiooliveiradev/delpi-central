from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class ChatSession:
    id: UUID
    user_id: UUID
    title: str | None
    context: str | None
    created_at: datetime
    updated_at: datetime
    project_id: UUID | None = None
    agent_id: UUID | None = None
    is_pinned: bool = False
    pinned_at: datetime | None = None
    archived_at: datetime | None = None
