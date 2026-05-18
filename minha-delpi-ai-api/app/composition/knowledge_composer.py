from app.application.use_cases.ingest_knowledge_document_use_case import (
    IngestKnowledgeDocumentUseCase,
)
from app.application.use_cases.search_knowledge_use_case import SearchKnowledgeUseCase
from app.composition.knowledge_pipeline_composer import (
    make_knowledge_ingestion_pipeline_service,
)
from app.infrastructure.embeddings.local_embedding_gateway import LocalEmbeddingGateway
from app.infrastructure.persistence.postgres_audit_repository import PostgresAuditRepository
from app.infrastructure.persistence.postgres_knowledge_repository import (
    PostgresKnowledgeRepository,
)


def make_ingest_knowledge_document_use_case() -> IngestKnowledgeDocumentUseCase:
    return IngestKnowledgeDocumentUseCase(
        knowledge_repository=PostgresKnowledgeRepository(),
        embedding_gateway=LocalEmbeddingGateway(),
        pipeline=make_knowledge_ingestion_pipeline_service(),
        audit_repository=PostgresAuditRepository(),
    )


def make_search_knowledge_use_case() -> SearchKnowledgeUseCase:
    return SearchKnowledgeUseCase(
        knowledge_repository=PostgresKnowledgeRepository(),
        embedding_gateway=LocalEmbeddingGateway(),
    )
