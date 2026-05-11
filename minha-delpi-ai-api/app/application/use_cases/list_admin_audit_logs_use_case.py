from app.domain.ports.audit_repository_port import AuditRepositoryPort


class ListAdminAuditLogsUseCase:
    def __init__(self, audit_repository: AuditRepositoryPort):
        self.audit_repository = audit_repository

    def execute(self, limit: int = 100) -> list[dict]:
        safe_limit = max(1, min(int(limit), 200))
        return self.audit_repository.list_logs(limit=safe_limit)
