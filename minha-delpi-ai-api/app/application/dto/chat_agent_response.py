from dataclasses import dataclass


@dataclass(frozen=True)
class ChatAgentResponse:
    id: str
    key: str
    name: str
    description: str | None
    enabled: bool
    metadata: dict | None
    created_at: str
    updated_at: str
