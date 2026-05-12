from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class ChatAgent:
    id: UUID
    key: str
    name: str
    description: str | None
    system_prompt: str | None
    enabled: bool
    metadata: dict | None
    created_at: datetime
    updated_at: datetime
