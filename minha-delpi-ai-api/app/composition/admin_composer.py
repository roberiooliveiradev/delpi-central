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


def make_list_admin_audit_logs_use_case() -> ListAdminAuditLogsUseCase:
    return ListAdminAuditLogsUseCase(PostgresAuditRepository())
