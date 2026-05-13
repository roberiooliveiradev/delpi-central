from dataclasses import dataclass


@dataclass(frozen=True)
class SearchKnowledgeRequest:
    query: str
    limit: int = 6
    filters: dict | None = None
