from __future__ import annotations

from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_approval_states_repository import (
    PurchaseRequestApprovalStatesRepository,
)


class ListSuppliesPurchaseRequestApprovalStatesUseCase:
    def __init__(
        self,
        repository: PurchaseRequestApprovalStatesRepository | None = None,
    ) -> None:
        self._repository = repository or PurchaseRequestApprovalStatesRepository()

    def execute(
        self,
        *,
        branches: list[str] | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int | None = None,
    ) -> dict:
        return self._repository.list_approval_states(
            branches=branches,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        )
