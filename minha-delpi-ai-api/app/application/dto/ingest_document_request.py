from dataclasses import dataclass


@dataclass(frozen=True)
class IngestDocumentRequest:
    title: str
    source_type: str
    source_ref: str | None
    content: str
    metadata: dict | None = None
