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
        filters: dict | None = None,
    ) -> list[KnowledgeChunk]:
        raise NotImplementedError

    @abstractmethod
    def search_keyword_chunks(
        self,
        query: str,
        limit: int,
        filters: dict | None = None,
    ) -> list[KnowledgeChunk]:
        raise NotImplementedError

    @abstractmethod
    def list_documents(self, limit: int = 100) -> list[KnowledgeDocument]:
        raise NotImplementedError

    @abstractmethod
    def list_documents_with_chunk_count(
        self,
        limit: int = 100,
        offset: int = 0,
        search: str | None = None,
        active: bool | None = None,
        scope: str | None = None,
        curatorial_filters: dict | None = None,
    ) -> list[tuple[KnowledgeDocument, int]]:
        raise NotImplementedError

    @abstractmethod
    def count_documents(
        self,
        search: str | None = None,
        active: bool | None = None,
        scope: str | None = None,
        curatorial_filters: dict | None = None,
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    def update_document_metadata(
        self,
        document_id: UUID,
        metadata: dict,
    ) -> KnowledgeDocument | None:
        raise NotImplementedError

    @abstractmethod
    def update_document(
        self,
        document_id: UUID,
        *,
        content: str | None = None,
        metadata: dict | None = None,
    ) -> KnowledgeDocument | None:
        raise NotImplementedError

    @abstractmethod
    def get_global_curatorial_facets(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    def list_documents_by_metadata(
        self,
        *,
        filters: dict,
        limit: int = 100,
        active: bool | None = True,
    ) -> list[tuple[KnowledgeDocument, int]]:
        raise NotImplementedError

    @abstractmethod
    def get_document_by_id(self, document_id: UUID) -> KnowledgeDocument | None:
        raise NotImplementedError

    @abstractmethod
    def list_chunks_by_document_id(
        self,
        document_id: UUID,
        *,
        limit: int = 12,
    ) -> list[KnowledgeChunk]:
        raise NotImplementedError

    @abstractmethod
    def find_global_document_by_content_hash(
        self,
        content_hash: str,
        source_ref: str | None = None,
    ) -> KnowledgeDocument | None:
        raise NotImplementedError

    @abstractmethod
    def delete_chunks_by_document_id(self, document_id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete_document(self, document_id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    def deactivate_document(self, document_id: UUID) -> KnowledgeDocument | None:
        raise NotImplementedError

    @abstractmethod
    def reactivate_document(self, document_id: UUID) -> KnowledgeDocument | None:
        raise NotImplementedError
