from dataclasses import dataclass


@dataclass(frozen=True)
class ChatMessageResponse:
    id: str
    session_id: str
    role: str
    content: str
    metadata: dict | None
    created_at: str
    user_feedback: int | None = None
    user_feedback_reason: str | None = None
    branch: dict | None = None
    parent_message_id: str | None = None
