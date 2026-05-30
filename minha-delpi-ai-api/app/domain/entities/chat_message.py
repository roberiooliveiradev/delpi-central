from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class ChatMessage:
    id: UUID
    session_id: UUID
    role: str
    content: str
    metadata: dict | None
    created_at: datetime
    parent_message_id: UUID | None = None
