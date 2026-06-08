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
from app.domain.ports.chat_quality_report_repository_port import ChatQualityReportRepositoryPort
from app.domain.ports.chat_skill_repository_port import ChatSkillRepositoryPort
from app.domain.ports.external_action_repository_port import ExternalActionRepositoryPort
from app.infrastructure.persistence.postgres_audit_repository import PostgresAuditRepository
from app.infrastructure.persistence.postgres_chat_agent_repository import (
    PostgresChatAgentRepository,
)
from app.infrastructure.persistence.postgres_chat_quality_report_repository import (
    PostgresChatQualityReportRepository,
)
from app.infrastructure.persistence.postgres_chat_skill_repository import PostgresChatSkillRepository


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
