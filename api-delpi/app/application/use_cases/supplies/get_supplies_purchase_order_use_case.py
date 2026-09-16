from __future__ import annotations

from app.domain.totvs.protheus_branches import PROTHEUS_BRANCH_CODES
from app.infrastructure.persistence.totvs.supplies_repositories.purchase_orders_list_repository import (
    PurchaseOrdersListRepository,
)


class GetSuppliesPurchaseOrderUseCase:
    def __init__(self, repository: PurchaseOrdersListRepository | None = None) -> None:
        self._repository = repository or PurchaseOrdersListRepository()

    def execute(self, *, branch: str, order_number: str) -> dict | None:
        normalized_branch = (branch or "").strip()
        normalized_number = (order_number or "").strip()
        if not normalized_branch or not normalized_number:
            raise ValueError("branch and order_number are required")
        if normalized_branch not in PROTHEUS_BRANCH_CODES:
            raise ValueError("invalid branch")
        return self._repository.get_open_order(
            branch=normalized_branch,
            order_number=normalized_number,
        )
