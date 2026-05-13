from dataclasses import dataclass


@dataclass(frozen=True)
class CreateChatAttachmentRequest:
    user_id: str
    session_id: str
    original_filename: str
    content_type: str | None
    size_bytes: int
    content: bytes
    metadata: dict | None = None
