from dataclasses import dataclass


@dataclass(frozen=True)
class ChatSessionResponse:
    id: str
    title: str | None
    context: str | None
    project_id: str | None
    agent_id: str | None
    is_pinned: bool
    pinned_at: str | None
    archived_at: str | None
    created_at: str
    updated_at: str
