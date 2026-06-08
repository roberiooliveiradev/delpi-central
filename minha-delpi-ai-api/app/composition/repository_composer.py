from __future__ import annotations

from app.application.use_cases.list_external_action_providers_use_case import (
    ListExternalActionProvidersUseCase,
)
from app.application.use_cases.list_external_actions_use_case import (
    ListExternalActionsUseCase,
)
from app.composition.external_action_composer import make_postgres_external_action_repository
from app.infrastructure.persistence.postgres_audit_repository import PostgresAuditRepository
from app.infrastructure.persistence.postgres_chat_agent_repository import (
    PostgresChatAgentRepository,
)
from app.infrastructure.persistence.postgres_chat_quality_report_repository import (
    PostgresChatQualityReportRepository,
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
