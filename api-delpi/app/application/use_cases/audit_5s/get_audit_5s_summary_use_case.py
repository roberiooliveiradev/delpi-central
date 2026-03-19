# app/application/use_cases/auditoria_5s/get_audit_5s_summary_use_case.py
from app.application.dto.auditoria_5s.audit_5s_summary_request import (
    Audit5SSummaryRequest,
)
from app.application.dto.auditoria_5s.audit_5s_summary_response import (
    Audit5SSummaryResponse,
)
from app.domain.ports.audit_5s.audit_5s_query_port import (
    Audit5SQueryRepositoryPort,
)


class GetAudit5SSummaryUseCase:
    def __init__(self, repository: Audit5SQueryRepositoryPort):
        self.repository = repository

    def execute(
        self,
        request: Audit5SSummaryRequest,
    ) -> Audit5SSummaryResponse:
        return self.repository.get_audit_summary(request)