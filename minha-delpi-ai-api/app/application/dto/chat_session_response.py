from dataclasses import dataclass


@dataclass(frozen=True)
class ChatSessionResponse:
    id: str
    title: str | None
    context: str | None
    created_at: str
    updated_at: str
