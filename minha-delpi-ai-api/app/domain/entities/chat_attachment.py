from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class ChatAttachment:
    id: UUID
    user_id: UUID
    session_id: UUID
    message_id: UUID | None
    project_id: UUID | None
    agent_id: UUID | None
    filename: str
    original_filename: str
    content_type: str | None
    size_bytes: int
    storage_path: str
    status: str
    metadata: dict | None
    created_at: datetime
    updated_at: datetime
