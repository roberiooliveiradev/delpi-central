from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class KnowledgeChunk:
    id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    metadata: dict | None
    created_at: datetime
    score: float | None = None
    title: str | None = None
    source_type: str | None = None
    source_ref: str | None = None
