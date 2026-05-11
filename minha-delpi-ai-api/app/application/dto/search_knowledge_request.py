from dataclasses import dataclass


@dataclass(frozen=True)
class SearchKnowledgeRequest:
    query: str
    limit: int = 6
