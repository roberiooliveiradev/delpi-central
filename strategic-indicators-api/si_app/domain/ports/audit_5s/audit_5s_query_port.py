# app/domain/ports/auditoria_5s/audit_5s_query_port.py
from abc import ABC, abstractmethod

from si_app.application.dto.auditoria_5s.audit_5s_summary_request import (
    Audit5SSummaryRequest,
)
from si_app.application.dto.auditoria_5s.audit_5s_summary_response import (
    Audit5SSummaryResponse,
)


class Audit5SQueryRepositoryPort(ABC):

    @abstractmethod
    def get_audit_summary(
        self,
        request: Audit5SSummaryRequest,
    ) -> Audit5SSummaryResponse:
        raise NotImplementedError