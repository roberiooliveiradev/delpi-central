"""Use case — products with process inspection plan."""

from __future__ import annotations

from app.application.use_cases.process_inspection_plans.list_process_inspection_plans_products_use_case import (
    ListProcessInspectionPlansProductsUseCase,
)


class _FakeRepo:
    def count_products_with_plan(self) -> int:
        return 1

    def list_products_with_plan(self, *, page: int, page_size: int):
        return [
            {
                "product_code": "8001",
                "product_description": "Desc",
                "revision": "001",
                "description": "Plan",
                "inspection_type": "P",
                "created_at": "20240101",
                "start_date": "20240101",
            }
        ]


def test_list_products_with_plan_use_case() -> None:
    uc = ListProcessInspectionPlansProductsUseCase(repository=_FakeRepo())
    data = uc.execute(page=1, page_size=50).to_dict()
    assert data["items"][0]["revision"] == "001"
