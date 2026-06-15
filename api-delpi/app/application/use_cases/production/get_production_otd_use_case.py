from __future__ import annotations

from app.application.dto.production.get_production_otd_request import (
    GetProductionOtdRequest,
)
from app.application.dto.production.production_request import ProductionRequest
from app.application.shared.numeric_parsing import to_optional_float
from app.domain.ports.production.on_time_delivery_repository_port import (
    OnTimeDeliveryRepositoryPort,
)


class GetProductionOtdUseCase:
    def __init__(
        self,
        on_time_delivery_repository: OnTimeDeliveryRepositoryPort,
    ):
        self._on_time_delivery_repository = on_time_delivery_repository

    def execute(self, request: GetProductionOtdRequest) -> dict:
        production_request = ProductionRequest(
            branch=request.branch,
            start_date=request.start_date,
            end_date=request.end_date,
        )

        if request.branch:
            summary_entity = self._on_time_delivery_repository.get_on_time_delivery(
                production_request
            )
            total_ops = int(summary_entity.total_ops_finished or 0)
            on_time_ops = int(summary_entity.on_time_ops or 0)
            late_ops = int(summary_entity.late_ops or 0)
            otd_pct = to_optional_float(summary_entity.on_time_delivery_pct)
        else:
            rows = self._on_time_delivery_repository.list_on_time_delivery_by_branch(
                production_request
            )
            total_ops = sum(int(row.get("total_ops_finished") or 0) for row in rows)
            on_time_ops = sum(int(row.get("on_time_ops") or 0) for row in rows)
            late_ops = sum(int(row.get("late_ops") or 0) for row in rows)
            otd_pct = (
                round(on_time_ops * 100.0 / total_ops, 2) if total_ops > 0 else None
            )

        late_percentage = (
            round(late_ops * 100.0 / total_ops, 2) if total_ops > 0 else 0.0
        )

        orders_page = self._on_time_delivery_repository.list_production_orders_otd(
            request
        )

        return {
            "branch": request.branch or "consolidated",
            "start_date": request.start_date or "",
            "end_date": request.end_date or "",
            "summary": {
                "total_ops_finished": total_ops,
                "on_time_ops": on_time_ops,
                "late_ops": late_ops,
                "on_time_delivery_pct": (
                    round(otd_pct, 2) if otd_pct is not None else None
                ),
                "late_percentage": late_percentage,
            },
            "orders": orders_page.to_dict(),
        }
