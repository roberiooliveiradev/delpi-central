from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ChatAttachmentResponse:
    id: str
    session_id: str
    message_id: str | None
    project_id: str | None
    agent_id: str | None
    filename: str
    original_filename: str
    content_type: str | None
    size_bytes: int
    status: str
    metadata: dict | None
    created_at: datetime
    updated_at: datetime
