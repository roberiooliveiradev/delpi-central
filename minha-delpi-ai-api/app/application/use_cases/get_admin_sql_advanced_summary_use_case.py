from app.domain.ports.audit_repository_port import AuditRepositoryPort
from app.infrastructure.config.settings import Settings


class GetAdminSqlAdvancedSummaryUseCase:
    def __init__(self, audit_repository: AuditRepositoryPort):
        self.audit_repository = audit_repository

    def execute(self, *, hours: int = 168) -> dict:
        safe_hours = max(1, min(int(hours), Settings.ADMIN_METRICS_MAX_HOURS))

        return self.audit_repository.get_sql_advanced_summary(hours=safe_hours)
