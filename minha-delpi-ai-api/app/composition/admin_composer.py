from app.infrastructure.persistence.postgres_external_action_repository import PostgresExternalActionRepository
from app.domain.services.external_actions.external_provider_url_policy import ExternalProviderUrlPolicy
from app.application.use_cases.list_external_actions_use_case import ListExternalActionsUseCase
from app.application.use_cases.list_external_action_providers_use_case import ListExternalActionProvidersUseCase
from app.application.use_cases.import_external_actions_schema_use_case import ImportExternalActionsSchemaUseCase
from app.application.use_cases.create_external_action_provider_use_case import CreateExternalActionProviderUseCase
from app.application.use_cases.deactivate_knowledge_document_use_case import (
    DeactivateKnowledgeDocumentUseCase,
)
from app.application.use_cases.get_admin_metrics_summary_use_case import GetAdminMetricsSummaryUseCase
from app.application.use_cases.get_admin_system_check_use_case import GetAdminSystemCheckUseCase
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
from app.infrastructure.config.settings import Settings
from app.infrastructure.embeddings.local_embedding_gateway import LocalEmbeddingGateway
from app.infrastructure.persistence.postgres_admin_metrics_repository import PostgresAdminMetricsRepository
from app.infrastructure.persistence.postgres_admin_system_check_repository import PostgresAdminSystemCheckRepository
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
        chunker=TextChunkerService(chunk_size=Settings.KNOWLEDGE_CHUNK_SIZE, overlap=Settings.KNOWLEDGE_CHUNK_OVERLAP),
        audit_repository=PostgresAuditRepository(),
    )


def make_list_admin_audit_logs_use_case() -> ListAdminAuditLogsUseCase:
    return ListAdminAuditLogsUseCase(PostgresAuditRepository())

def make_get_admin_metrics_summary_use_case() -> GetAdminMetricsSummaryUseCase:
    return GetAdminMetricsSummaryUseCase(PostgresAdminMetricsRepository())

def make_get_admin_system_check_use_case() -> GetAdminSystemCheckUseCase:
    return GetAdminSystemCheckUseCase(PostgresAdminSystemCheckRepository())

def make_create_external_action_provider_use_case() -> CreateExternalActionProviderUseCase:
    return CreateExternalActionProviderUseCase(
        repository=PostgresExternalActionRepository(),
        url_policy=ExternalProviderUrlPolicy(),
    )


def make_list_external_action_providers_use_case() -> ListExternalActionProvidersUseCase:
    return ListExternalActionProvidersUseCase(PostgresExternalActionRepository())


def make_import_external_actions_schema_use_case() -> ImportExternalActionsSchemaUseCase:
    return ImportExternalActionsSchemaUseCase(PostgresExternalActionRepository())


def make_list_external_actions_use_case() -> ListExternalActionsUseCase:
    return ListExternalActionsUseCase(PostgresExternalActionRepository())

