import math

from app.domain.ports.embedding_gateway_port import EmbeddingGatewayPort
from app.domain.ports.knowledge_repository_port import KnowledgeRepositoryPort
from app.infrastructure.config.settings import Settings


class KnowledgeSemanticDeduplicatorService:
    def __init__(
        self,
        *,
        embedding_gateway: EmbeddingGatewayPort,
        knowledge_repository: KnowledgeRepositoryPort,
    ):
        self.embedding_gateway = embedding_gateway
        self.knowledge_repository = knowledge_repository

    def find_near_duplicates(
        self,
        *,
        content: str,
        limit: int = 5,
        threshold: float | None = None,
    ) -> list[dict]:
        normalized = " ".join(str(content or "").split())

        if len(normalized) < 40:
            return []

        safe_threshold = threshold if threshold is not None else Settings.KNOWLEDGE_SEMANTIC_DEDUP_THRESHOLD
        embedding = self.embedding_gateway.embed(normalized[:4000])
        matches = self.knowledge_repository.search_similar_chunks(
            embedding=embedding,
            limit=max(1, min(limit, 10)),
            filters={"active_only": True},
        )

        duplicates: list[dict] = []

        for match in matches:
            similarity = float(match.score or 0)

            if similarity < safe_threshold:
                continue

            duplicates.append(
                {
                    "documentId": str(match.document_id),
                    "chunkId": str(match.id),
                    "title": match.title,
                    "sourceType": match.source_type,
                    "similarity": round(similarity, 4),
                    "preview": self._truncate(match.content or "", 240),
                }
            )

        return duplicates

    def _truncate(self, value: str, max_chars: int) -> str:
        normalized = " ".join(str(value or "").split())

        if len(normalized) <= max_chars:
            return normalized

        return f"{normalized[: max_chars - 1].rstrip()}…"
