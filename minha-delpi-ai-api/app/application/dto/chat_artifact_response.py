from dataclasses import dataclass


@dataclass(frozen=True)
class ChatArtifactResponse:
    id: str
    session_id: str
    message_id: str | None
    user_id: str
    type: str
    title: str
    content: str
    metadata: dict | None
    created_at: str
    updated_at: str
