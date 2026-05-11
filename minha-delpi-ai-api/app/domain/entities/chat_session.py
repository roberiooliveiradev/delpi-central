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
