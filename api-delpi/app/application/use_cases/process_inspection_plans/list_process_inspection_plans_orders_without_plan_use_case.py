from __future__ import annotations

from typing import Any

from app.application.dto.process_inspection_plans.process_inspection_plans_list_responses import (
    ProcessInspectionPlansOrdersWithoutPlanItem,
    ProcessInspectionPlansOrdersWithoutPlanResponse,
    build_pagination,
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


class ListProcessInspectionPlansOrdersWithoutPlanUseCase:
    def __init__(self, repository: ProcessInspectionPlansRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        branch: str | None,
        page: int,
        page_size: int,
    ) -> ProcessInspectionPlansOrdersWithoutPlanResponse:
        scope = normalize_optional_branch(branch)
        total = self._repository.count_orders_without_plan(scope)
        rows = self._repository.list_orders_without_plan(
            scope,
            page=page,
            page_size=page_size,
        )
        items = [
            ProcessInspectionPlansOrdersWithoutPlanItem(
                branch=str(row.get("branch") or ""),
                product_code=str(row.get("product_code") or ""),
                product_description=row.get("product_description"),
                production_order=str(row.get("production_order") or ""),
                observation=row.get("observation"),
            )
            for row in rows
        ]
        return ProcessInspectionPlansOrdersWithoutPlanResponse(
            branch=scope,
            items=items,
            pagination=build_pagination(page=page, page_size=page_size, total=total),
        )
