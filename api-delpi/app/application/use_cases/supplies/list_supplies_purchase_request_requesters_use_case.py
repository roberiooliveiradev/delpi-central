from __future__ import annotations

from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_lines_repository import (
    PurchaseRequestLinesRepository,
)


class ListSuppliesPurchaseRequestRequestersUseCase:
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
        product_code: str | None = None,
        supplier_code: str | None = None,
        order_number: str | None = None,
    ) -> dict:
        items = self._repository.list_requesters(
            branch=branch,
            date_from=date_from,
            date_to=date_to,
            cost_centers=cost_centers,
            request_number=request_number,
            product_code=product_code,
            supplier_code=supplier_code,
            order_number=order_number,
        )
        return {"items": items}
