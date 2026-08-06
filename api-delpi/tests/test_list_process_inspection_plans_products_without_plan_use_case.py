"""Use case — products without process inspection plan."""

from __future__ import annotations

from app.application.use_cases.process_inspection_plans.list_process_inspection_plans_products_without_plan_use_case import (
    ListProcessInspectionPlansProductsWithoutPlanUseCase,
)


class _FakeRepo:
    def count_products_without_plan(self, branch_scope: str) -> int:
        return 1

    def list_products_without_plan(self, branch_scope: str, *, page: int, page_size: int):
        return [
            {
                "product_code": "8001",
                "product_description": "Desc",
                "open_orders_count": 2,
            }
        ]


def test_list_products_without_plan_use_case() -> None:
    uc = ListProcessInspectionPlansProductsWithoutPlanUseCase(repository=_FakeRepo())
    data = uc.execute(branch="01", page=1, page_size=50).to_dict()
    assert data["items"][0]["open_orders_count"] == 2
    assert data["pagination"]["total"] == 1
