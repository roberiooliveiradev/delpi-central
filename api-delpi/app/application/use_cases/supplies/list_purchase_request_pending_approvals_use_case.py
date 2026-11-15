from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_pending_approvals_repository import (
    PurchaseRequestPendingApprovalsRepository,
)


class ListPurchaseRequestPendingApprovalsUseCase:
    def __init__(self, repository=None):
        self._repository = repository or PurchaseRequestPendingApprovalsRepository()

    def execute(self, *, after_branch="", after_request_number="", limit=25):
        return self._repository.list_pending_approvals(
            after_branch=after_branch,
            after_request_number=after_request_number,
            limit=limit,
        )
