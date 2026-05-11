from app.application.use_cases.deactivate_knowledge_document_use_case import (
    DeactivateKnowledgeDocumentUseCase,
)
from app.application.use_cases.get_llm_provider_status_use_case import (
    GetLlmProviderStatusUseCase,
)
from app.application.use_cases.list_admin_audit_logs_use_case import (
    ListAdminAuditLogsUseCase,
)
from app.application.use_cases.list_admin_knowledge_documents_use_case import (
    ListAdminKnowledgeDocumentsUseCase,
)
from app.application.use_cases.reactivate_knowledge_document_use_case import (
    ReactivateKnowledgeDocumentUseCase,
)
from app.application.use_cases.reindex_knowledge_document_use_case import (
    ReindexKnowledgeDocumentUseCase,
)
from app.domain.services.text_chunker_service import TextChunkerService
from app.infrastructure.embeddings.local_embedding_gateway import LocalEmbeddingGateway
from app.infrastructure.persistence.postgres_audit_repository import PostgresAuditRepository
from app.infrastructure.persistence.postgres_knowledge_repository import (
    PostgresKnowledgeRepository,
)


def make_get_llm_provider_status_use_case() -> GetLlmProviderStatusUseCase:
    return GetLlmProviderStatusUseCase()


def make_list_admin_knowledge_documents_use_case() -> ListAdminKnowledgeDocumentsUseCase:
    return ListAdminKnowledgeDocumentsUseCase(PostgresKnowledgeRepository())


def make_deactivate_knowledge_document_use_case() -> DeactivateKnowledgeDocumentUseCase:
    return DeactivateKnowledgeDocumentUseCase(
        knowledge_repository=PostgresKnowledgeRepository(),
        audit_repository=PostgresAuditRepository(),
    )


def make_reactivate_knowledge_document_use_case() -> ReactivateKnowledgeDocumentUseCase:
    return ReactivateKnowledgeDocumentUseCase(
        knowledge_repository=PostgresKnowledgeRepository(),
        audit_repository=PostgresAuditRepository(),
    )


def make_reindex_knowledge_document_use_case() -> ReindexKnowledgeDocumentUseCase:
    return ReindexKnowledgeDocumentUseCase(
        knowledge_repository=PostgresKnowledgeRepository(),
        embedding_gateway=LocalEmbeddingGateway(),
        chunker=TextChunkerService(),
        audit_repository=PostgresAuditRepository(),
    )


def make_list_admin_audit_logs_use_case() -> ListAdminAuditLogsUseCase:
    return ListAdminAuditLogsUseCase(PostgresAuditRepository())
