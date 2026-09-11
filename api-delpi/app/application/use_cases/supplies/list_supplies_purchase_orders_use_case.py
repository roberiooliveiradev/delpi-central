from __future__ import annotations

from app.infrastructure.persistence.totvs.supplies_repositories.purchase_orders_list_repository import (
    PurchaseOrdersListRepository,
)


class ListSuppliesPurchaseOrdersUseCase:
    def __init__(self, repository: PurchaseOrdersListRepository | None = None) -> None:
        self._repository = repository or PurchaseOrdersListRepository()

    def execute(
        self,
        *,
        branch: str,
        order_number: str | None = None,
        product_code: str | None = None,
        supplier_code: str | None = None,
        expected_delivery_from: str | None = None,
        expected_delivery_to: str | None = None,
        late_only: bool = False,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        return self._repository.list_open_lines(
            branch=branch,
            order_number=order_number,
            product_code=product_code,
            supplier_code=supplier_code,
            expected_delivery_from=expected_delivery_from,
            expected_delivery_to=expected_delivery_to,
            late_only=late_only,
            page=page,
            page_size=page_size,
        )
