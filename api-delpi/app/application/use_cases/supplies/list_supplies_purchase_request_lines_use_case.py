from __future__ import annotations

from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_lines_repository import (
    PurchaseRequestLinesRepository,
)


class ListSuppliesPurchaseRequestLinesUseCase:
    def __init__(self, repository: PurchaseRequestLinesRepository | None = None) -> None:
        self._repository = repository or PurchaseRequestLinesRepository()

    def execute(
        self,
        *,
        branch: str,
        date_from: str | None = None,
        date_to: str | None = None,
        cost_centers: list[str] | None = None,
        request_number: str | None = None,
        requester_protheus_user_ids: list[str] | None = None,
        product_code: str | None = None,
        supplier_code: str | None = None,
        order_number: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        return self._repository.list_lines(
            branch=branch,
            date_from=date_from,
            date_to=date_to,
            cost_centers=cost_centers,
            request_number=request_number,
            requester_protheus_user_ids=requester_protheus_user_ids,
            product_code=product_code,
            supplier_code=supplier_code,
            order_number=order_number,
            page=page,
            page_size=page_size,
        )
