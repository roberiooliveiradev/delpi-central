from app.application.use_cases.ingest_knowledge_document_use_case import (
    IngestKnowledgeDocumentUseCase,
)
from app.application.use_cases.search_knowledge_use_case import SearchKnowledgeUseCase
from app.domain.services.text_chunker_service import TextChunkerService
from app.infrastructure.config.settings import Settings
from app.infrastructure.embeddings.local_embedding_gateway import LocalEmbeddingGateway
from app.infrastructure.persistence.postgres_audit_repository import PostgresAuditRepository
from app.infrastructure.persistence.postgres_knowledge_repository import (
    PostgresKnowledgeRepository,
)


def make_ingest_knowledge_document_use_case() -> IngestKnowledgeDocumentUseCase:
    return IngestKnowledgeDocumentUseCase(
        knowledge_repository=PostgresKnowledgeRepository(),
        embedding_gateway=LocalEmbeddingGateway(),
        chunker=TextChunkerService(
            chunk_size=Settings.KNOWLEDGE_CHUNK_SIZE,
            overlap=Settings.KNOWLEDGE_CHUNK_OVERLAP,
        ),
        audit_repository=PostgresAuditRepository(),
    )


def make_search_knowledge_use_case() -> SearchKnowledgeUseCase:
    return SearchKnowledgeUseCase(
        knowledge_repository=PostgresKnowledgeRepository(),
        embedding_gateway=LocalEmbeddingGateway(),
    )
