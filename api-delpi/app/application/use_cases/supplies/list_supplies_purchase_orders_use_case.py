from __future__ import annotations

from datetime import date

from app.infrastructure.persistence.totvs.supplies_repositories.purchase_orders_list_repository import (
    PurchaseOrdersListRepository,
)


class ListSuppliesPurchaseOrdersUseCase:
    def __init__(self, repository: PurchaseOrdersListRepository | None = None) -> None:
        self._repository = repository or PurchaseOrdersListRepository()

    def execute(
        self,
        *,
        branch: str | None = None,
        branches: list[str] | None = None,
        order_number: str | None = None,
        product_code: str | None = None,
        supplier_code: str | None = None,
        expected_delivery_from: str | None = None,
        expected_delivery_to: str | None = None,
        late_only: bool = False,
        sort_by: str | None = None,
        sort_dir: str | None = None,
        page: int = 1,
        page_size: int = 50,
        reference: date | None = None,
    ) -> dict:
        return self._repository.list_open_lines(
            branch=branch,
            branches=branches,
            order_number=order_number,
            product_code=product_code,
            supplier_code=supplier_code,
            expected_delivery_from=expected_delivery_from,
            expected_delivery_to=expected_delivery_to,
            late_only=late_only,
            sort_by=sort_by,
            sort_dir=sort_dir,
            page=page,
            page_size=page_size,
            reference=reference,
        )

    def export(
        self,
        *,
        branch: str | None = None,
        branches: list[str] | None = None,
        order_number: str | None = None,
        product_code: str | None = None,
        supplier_code: str | None = None,
        expected_delivery_from: str | None = None,
        expected_delivery_to: str | None = None,
        late_only: bool = False,
        sort_by: str | None = None,
        sort_dir: str | None = None,
        reference: date | None = None,
    ) -> dict:
        return self._repository.export_open_lines(
            branch=branch,
            branches=branches,
            order_number=order_number,
            product_code=product_code,
            supplier_code=supplier_code,
            expected_delivery_from=expected_delivery_from,
            expected_delivery_to=expected_delivery_to,
            late_only=late_only,
            sort_by=sort_by,
            sort_dir=sort_dir,
            reference=reference,
        )
