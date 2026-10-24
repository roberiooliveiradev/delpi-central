from typing import Literal

from pydantic import BaseModel, Field


class KnowledgeExcerpt(BaseModel):
    section: str
    heading: str
    line_start: int
    line_end: int
    chunk: int
    text: str = Field(description="Untrusted, escaped plain-text guidance; at most 4096 UTF-8 bytes.")
    sanitized: Literal[True]


class GovernedKnowledgePage(BaseModel):
    knowledge_kind: Literal["GUIDANCE"]
    authority: Literal["GUIDANCE_NOT_DOMAIN_TRUTH"]
    trust_level: Literal["UNTRUSTED_DOCUMENT_CONTENT"]
    content_format: Literal["plain_text"]
    topic: str
    corpus_id: str
    corpus_version: Literal[1]
    manifest_identity: str
    source_path: str
    source_git_sha: str
    source_sha256: str
    items: list[KnowledgeExcerpt]
    page: int
    page_size: int
    total: int
    has_more: bool
    coverage: Literal["PARTIAL", "COMPLETE_SELECTION"]
    selection: Literal["section", "document"]


class GovernedKnowledgeEnvelope(BaseModel):
    success: bool
    message: str
    data: GovernedKnowledgePage
    error: dict | None = None
    meta: dict
