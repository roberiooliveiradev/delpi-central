from dataclasses import dataclass


@dataclass(frozen=True)
class ChatSourceResponse:
    id: str
    title: str
    source_type: str
    source_ref: str | None
    scope: str | None
    project_id: str | None
    agent_key: str | None
    attachment_id: str | None
    original_filename: str | None
    content_type: str | None
    active: bool
    metadata: dict | None
    created_at: str
    updated_at: str
    chunk_count: int | None = None
    indexed: bool | None = None
    extractor: dict | None = None
    index_reason: str | dict | None = None
