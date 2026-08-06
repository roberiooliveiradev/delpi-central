from __future__ import annotations

from typing import Any

from app.application.dto.process_inspection_plans.process_inspection_plans_summary_response import (
    ProcessInspectionPlansSummaryResponse,
)
from app.domain.ports.process_inspection_plans.process_inspection_plans_repository_port import (
    ProcessInspectionPlansRepositoryPort,
)
from app.domain.quality.process_inspection_plans.process_inspection_plans_scope import (
    normalize_optional_branch,
)


def _as_int(value: Any) -> int:
    if value is None or value == "":
        return 0
    return int(value)


class GetProcessInspectionPlansSummaryUseCase:
    def __init__(self, repository: ProcessInspectionPlansRepositoryPort) -> None:
        self._repository = repository

    def execute(self, *, branch: str | None) -> ProcessInspectionPlansSummaryResponse:
        scope = normalize_optional_branch(branch)
        row = self._repository.get_summary(scope)
        total = _as_int(row.get("total_open_orders"))
        without = _as_int(row.get("orders_without_plan"))
        with_plan = _as_int(row.get("orders_with_plan"))
        products_without = _as_int(row.get("products_without_plan"))
        registered_pct = (
            round(((total - without) / total) * 100, 2) if total else 0.0
        )
        distribution = [
            {
                "status": "with_plan",
                "label": "with_plan",
                "count": with_plan,
                "pct": round((with_plan / total) * 100, 2) if total else 0.0,
            },
            {
                "status": "without_plan",
                "label": "without_plan",
                "count": without,
                "pct": round((without / total) * 100, 2) if total else 0.0,
            },
        ]
        return ProcessInspectionPlansSummaryResponse(
            branch=scope,
            products_without_plan=products_without,
            orders_without_plan=without,
            total_open_orders=total,
            orders_with_plan=with_plan,
            registered_pct=registered_pct,
            distribution=distribution,
        )
