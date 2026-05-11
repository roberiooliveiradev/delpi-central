from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.knowledge_chunk import KnowledgeChunk
from app.domain.entities.knowledge_document import KnowledgeDocument


class KnowledgeRepositoryPort(ABC):
    @abstractmethod
    def create_document(
        self,
        title: str,
        source_type: str,
        source_ref: str | None,
        content: str,
        metadata: dict | None = None,
    ) -> KnowledgeDocument:
        raise NotImplementedError

    @abstractmethod
    def create_chunk(
        self,
        document_id: UUID,
        chunk_index: int,
        content: str,
        embedding: list[float],
        metadata: dict | None = None,
    ) -> KnowledgeChunk:
        raise NotImplementedError

    @abstractmethod
    def search_similar_chunks(
        self,
        embedding: list[float],
        limit: int,
    ) -> list[KnowledgeChunk]:
        raise NotImplementedError
