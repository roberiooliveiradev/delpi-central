from __future__ import annotations

from app.application.dto.process_inspection_plans.process_inspection_plans_list_responses import (
    ProcessInspectionPlansProductListItem,
    ProcessInspectionPlansProductsResponse,
    build_pagination,
)
from app.domain.ports.process_inspection_plans.process_inspection_plans_repository_port import (
    ProcessInspectionPlansRepositoryPort,
)


class ListProcessInspectionPlansProductsUseCase:
    def __init__(self, repository: ProcessInspectionPlansRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        page: int,
        page_size: int,
    ) -> ProcessInspectionPlansProductsResponse:
        total = self._repository.count_products_with_plan()
        rows = self._repository.list_products_with_plan(page=page, page_size=page_size)
        items = [
            ProcessInspectionPlansProductListItem(
                product_code=str(row.get("product_code") or ""),
                product_description=row.get("product_description"),
                revision=str(row.get("revision") or ""),
                description=row.get("description"),
                inspection_type=row.get("inspection_type"),
                created_at=row.get("created_at"),
                start_date=row.get("start_date"),
            )
            for row in rows
        ]
        return ProcessInspectionPlansProductsResponse(
            items=items,
            pagination=build_pagination(page=page, page_size=page_size, total=total),
        )
