"""Query only, no ERP writes or synthetic/polling approvals (HD #1004)."""

from __future__ import annotations

from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_approval_lead_time_repository import (
    PurchaseRequestApprovalLeadTimeRepository,
)


class GetPurchaseRequestApprovalLeadTimeUseCase:
    def __init__(self, repository: PurchaseRequestApprovalLeadTimeRepository | None = None):
        self._repository = repository or PurchaseRequestApprovalLeadTimeRepository()

    def execute(
        self,
        *,
        branches: list[str],
        date_from: str | None = None,
        date_to: str | None = None,
        request_number: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> dict:
        return self._repository.get_lead_time(
            branches=branches,
            date_from=date_from,
            date_to=date_to,
            request_number=request_number,
            page=page,
            page_size=page_size,
        )
