from dataclasses import dataclass


@dataclass(frozen=True)
class CreateChatArtifactRequest:
    user_id: str
    session_id: str
    type: str
    title: str
    content: str
    message_id: str | None = None
    metadata: dict | None = None
