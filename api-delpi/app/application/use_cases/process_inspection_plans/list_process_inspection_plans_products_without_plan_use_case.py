from __future__ import annotations

from typing import Any

from app.application.dto.process_inspection_plans.process_inspection_plans_list_responses import (
    ProcessInspectionPlansProductsWithoutPlanItem,
    ProcessInspectionPlansProductsWithoutPlanResponse,
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


class ListProcessInspectionPlansProductsWithoutPlanUseCase:
    def __init__(self, repository: ProcessInspectionPlansRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        branch: str | None,
        page: int,
        page_size: int,
    ) -> ProcessInspectionPlansProductsWithoutPlanResponse:
        scope = normalize_optional_branch(branch)
        total = self._repository.count_products_without_plan(scope)
        rows = self._repository.list_products_without_plan(
            scope,
            page=page,
            page_size=page_size,
        )
        items = [
            ProcessInspectionPlansProductsWithoutPlanItem(
                product_code=str(row.get("product_code") or ""),
                product_description=row.get("product_description"),
                open_orders_count=_as_int(row.get("open_orders_count")),
            )
            for row in rows
        ]
        return ProcessInspectionPlansProductsWithoutPlanResponse(
            branch=scope,
            items=items,
            pagination=build_pagination(page=page, page_size=page_size, total=total),
        )
