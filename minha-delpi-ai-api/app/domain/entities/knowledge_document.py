from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class KnowledgeDocument:
    id: UUID
    title: str
    source_type: str
    source_ref: str | None
    content: str
    metadata: dict | None
    active: bool
    created_at: datetime
    updated_at: datetime
