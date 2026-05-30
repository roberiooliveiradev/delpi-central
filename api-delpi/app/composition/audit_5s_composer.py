from __future__ import annotations

from app.application.use_cases.audit_5s.get_audit_5s_dashboard_use_case import (
    GetAudit5sDashboardUseCase,
)
from app.infrastructure.persistence.plugins.repositories.audit_5s.postgres_audit_5s_repository import (
    PostgresAudit5sRepository,
)


def build_audit_5s_repository() -> PostgresAudit5sRepository:
    return PostgresAudit5sRepository()


def build_get_audit_5s_dashboard_use_case() -> GetAudit5sDashboardUseCase:
    return GetAudit5sDashboardUseCase(repository=build_audit_5s_repository())
