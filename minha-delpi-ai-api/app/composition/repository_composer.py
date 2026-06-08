from __future__ import annotations

from app.application.use_cases.list_external_action_providers_use_case import (
    ListExternalActionProvidersUseCase,
)
from app.application.use_cases.list_external_actions_use_case import (
    ListExternalActionsUseCase,
)
from app.composition.external_action_composer import make_postgres_external_action_repository
from app.domain.ports.audit_repository_port import AuditRepositoryPort
from app.domain.ports.chat_agent_repository_port import ChatAgentRepositoryPort
from app.domain.ports.chat_message_feedback_repository_port import (
    ChatMessageFeedbackRepositoryPort,
)
from app.domain.ports.chat_quality_issue_repository_port import ChatQualityIssueRepositoryPort
from app.domain.ports.chat_quality_report_repository_port import ChatQualityReportRepositoryPort
from app.domain.ports.chat_attachment_repository_port import ChatAttachmentRepositoryPort
from app.domain.ports.chat_skill_repository_port import ChatSkillRepositoryPort
from app.domain.ports.evaluation_case_repository_port import EvaluationCaseRepositoryPort
from app.domain.ports.external_action_repository_port import ExternalActionRepositoryPort
from app.domain.ports.fine_tuning_repository_port import FineTuningRepositoryPort
from app.domain.ports.knowledge_repository_port import KnowledgeRepositoryPort
from app.domain.ports.learning_candidate_repository_port import LearningCandidateRepositoryPort
from app.domain.ports.memory_item_repository_port import MemoryItemRepositoryPort
from app.domain.ports.vocabulary_term_repository_port import VocabularyTermRepositoryPort
from app.infrastructure.persistence.postgres_audit_repository import PostgresAuditRepository
from app.infrastructure.persistence.postgres_chat_agent_repository import (
    PostgresChatAgentRepository,
)
from app.infrastructure.persistence.postgres_chat_message_feedback_repository import (
    PostgresChatMessageFeedbackRepository,
)
from app.infrastructure.persistence.postgres_chat_quality_issue_repository import (
    PostgresChatQualityIssueRepository,
)
from app.infrastructure.persistence.postgres_chat_quality_report_repository import (
    PostgresChatQualityReportRepository,
)
from app.infrastructure.persistence.postgres_chat_attachment_repository import (
    PostgresChatAttachmentRepository,
)
from app.infrastructure.persistence.postgres_chat_skill_repository import PostgresChatSkillRepository
from app.infrastructure.persistence.postgres_evaluation_case_repository import (
    PostgresEvaluationCaseRepository,
)
from app.infrastructure.persistence.postgres_fine_tuning_repository import (
    PostgresFineTuningRepository,
)
from app.infrastructure.persistence.postgres_knowledge_repository import PostgresKnowledgeRepository
from app.infrastructure.persistence.postgres_learning_candidate_repository import (
    PostgresLearningCandidateRepository,
)
from app.infrastructure.persistence.postgres_memory_item_repository import (
    PostgresMemoryItemRepository,
)
from app.infrastructure.persistence.postgres_vocabulary_term_repository import (
    PostgresVocabularyTermRepository,
)


def make_postgres_audit_repository() -> PostgresAuditRepository:
    return PostgresAuditRepository()


def make_postgres_chat_agent_repository() -> PostgresChatAgentRepository:
    return PostgresChatAgentRepository()


def make_list_external_action_providers_use_case() -> ListExternalActionProvidersUseCase:
    return ListExternalActionProvidersUseCase(make_postgres_external_action_repository())


def make_list_external_actions_use_case() -> ListExternalActionsUseCase:
    return ListExternalActionsUseCase(make_postgres_external_action_repository())


def make_postgres_chat_quality_report_repository() -> PostgresChatQualityReportRepository:
    return PostgresChatQualityReportRepository()


def make_audit_repository() -> AuditRepositoryPort:
    return make_postgres_audit_repository()


def make_chat_agent_repository() -> ChatAgentRepositoryPort:
    return make_postgres_chat_agent_repository()


def make_external_action_repository() -> ExternalActionRepositoryPort:
    return make_postgres_external_action_repository()


def make_chat_quality_report_repository() -> ChatQualityReportRepositoryPort:
    return make_postgres_chat_quality_report_repository()


def make_chat_skill_repository() -> ChatSkillRepositoryPort:
    return PostgresChatSkillRepository()


def make_chat_message_feedback_repository() -> ChatMessageFeedbackRepositoryPort:
    return PostgresChatMessageFeedbackRepository()


def make_chat_quality_issue_repository() -> ChatQualityIssueRepositoryPort:
    return PostgresChatQualityIssueRepository()


def make_memory_item_repository() -> MemoryItemRepositoryPort:
    return PostgresMemoryItemRepository()


def make_vocabulary_term_repository() -> VocabularyTermRepositoryPort:
    return PostgresVocabularyTermRepository()


def make_learning_candidate_repository() -> LearningCandidateRepositoryPort:
    return PostgresLearningCandidateRepository()


def make_evaluation_case_repository() -> EvaluationCaseRepositoryPort:
    return PostgresEvaluationCaseRepository()


def make_fine_tuning_repository() -> FineTuningRepositoryPort:
    return PostgresFineTuningRepository()


def make_knowledge_repository() -> KnowledgeRepositoryPort:
    return PostgresKnowledgeRepository()


def make_chat_attachment_repository() -> ChatAttachmentRepositoryPort:
    return PostgresChatAttachmentRepository()
