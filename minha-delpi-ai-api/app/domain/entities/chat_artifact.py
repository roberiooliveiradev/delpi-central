from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class ChatArtifact:
    id: UUID
    session_id: UUID
    user_id: UUID
    type: str
    title: str
    content: str
    metadata: dict | None
    created_at: datetime
    updated_at: datetime
    message_id: UUID | None = None
