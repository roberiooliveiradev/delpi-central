from __future__ import annotations

from app.application.dto.process_inspection_plans.process_inspection_plans_list_responses import (
    ProcessInspectionPlansProductDetailResponse,
)
from app.domain.ports.process_inspection_plans.process_inspection_plans_repository_port import (
    ProcessInspectionPlansRepositoryPort,
)
from app.domain.ports.product.product_inspection_repository_port import (
    ProductInspectionRepositoryPort,
)


class GetProcessInspectionPlansProductUseCase:
    def __init__(
        self,
        *,
        plans_repository: ProcessInspectionPlansRepositoryPort,
        inspection_repository: ProductInspectionRepositoryPort,
    ) -> None:
        self._plans_repository = plans_repository
        self._inspection_repository = inspection_repository

    def execute(
        self,
        *,
        product_code: str,
        include_bom: bool = False,
    ) -> ProcessInspectionPlansProductDetailResponse | None:
        code = str(product_code or "").strip()
        if not code:
            raise ValueError("product_code is required.")
        if not self._plans_repository.product_has_plan(code):
            return None

        max_depth = 999 if include_bom else 0
        inspections = self._inspection_repository.fetch_inspection_rows(
            code=code,
            max_depth=max_depth,
        )
        items = [
            {
                "product_code": i.product_code,
                "bom_level": i.bom_level,
                "has_inspection": i.has_inspection,
                "header": i.header,
                "measurable_tests": i.measurable_tests,
                "textual_tests": i.textual_tests,
            }
            for i in inspections
        ]
        return ProcessInspectionPlansProductDetailResponse(
            product_code=code,
            include_bom=include_bom,
            items=items,
            total=len(items),
        )
