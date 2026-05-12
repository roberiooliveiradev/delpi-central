from dataclasses import dataclass


@dataclass(frozen=True)
class ChatProjectResponse:
    id: str
    name: str
    description: str | None
    created_at: str
    updated_at: str
