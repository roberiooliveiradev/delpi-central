from __future__ import annotations

from app.application.dto.production.get_production_order_by_op_request import (
    GetProductionOrderByOpRequest,
)
from app.domain.ports.production.production_orders_repository_port import (
    ProductionOrdersRepositoryPort,
)


class GetProductionOrderByOpUseCase:
    def __init__(self, production_orders_repository: ProductionOrdersRepositoryPort):
        self._production_orders_repository = production_orders_repository

    def execute(self, request: GetProductionOrderByOpRequest) -> dict | None:
        production_order = (request.production_order or "").strip()
        if not production_order:
            raise ValueError("production_order é obrigatório.")

        row = self._production_orders_repository.fetch_order_by_production_order(
            production_order=production_order,
            branch=request.branch,
            product_type=self._normalize_product_type(request.product_type),
        )
        if not row:
            return None

        linked_orders = (
            self._production_orders_repository.fetch_linked_pi_orders_by_production_order(
                production_order=production_order,
                branch=request.branch or row.get("branch"),
                sort_by=self._normalize_linked_sort_by(request.linked_sort_by),
                sort_dir=self._normalize_sort_dir(request.linked_sort_dir),
            )
        )

        on_time = sum(1 for item in linked_orders if item.get("otd_status") == "on_time")
        late = sum(1 for item in linked_orders if item.get("otd_status") == "late")
        open_ops = sum(1 for item in linked_orders if item.get("otd_status") == "open")

        return {
            "order": row,
            "linked_orders": linked_orders,
            "link_summary": {
                "order_number": row.get("order_number"),
                "link_field": "C2_NUM",
                "total_pi_orders": len(linked_orders),
                "on_time_ops": on_time,
                "late_ops": late,
                "open_ops": open_ops,
            },
            "related_routes": {
                "product_detail": f"/products/{row.get('product_code')}",
                "product_summary": f"/products/{row.get('product_code')}/summary",
                "product_guide": f"/products/{row.get('product_code')}/guide",
                "product_stock": f"/products/{row.get('product_code')}/stock",
                "product_production_status": (
                    f"/products/{row.get('product_code')}/production-status"
                ),
            },
        }

    @staticmethod
    def _normalize_product_type(
        product_type: str | None,
    ) -> str | None:
        if product_type is None:
            return None

        normalized = str(product_type).strip().upper()
        if normalized not in {"PA", "PI"}:
            raise ValueError("product_type deve ser PA ou PI.")

        return normalized

    @staticmethod
    def _normalize_sort_dir(sort_dir: str | None) -> str:
        normalized = str(sort_dir or "asc").strip().lower()
        if normalized not in {"asc", "desc"}:
            raise ValueError("linked_sort_dir deve ser asc ou desc.")
        return normalized

    @staticmethod
    def _normalize_linked_sort_by(sort_by: str | None) -> str | None:
        if sort_by is None:
            return None

        normalized = str(sort_by).strip().lower()
        if not normalized:
            return None

        allowed = {
            "status",
            "branch",
            "production_order",
            "product_code",
            "description",
            "due",
            "finish",
            "days",
            "qty",
        }
        if normalized not in allowed:
            raise ValueError(
                "linked_sort_by inválido. Use: status, branch, production_order, "
                "product_code, description, due, finish, days ou qty."
            )

        return normalized
