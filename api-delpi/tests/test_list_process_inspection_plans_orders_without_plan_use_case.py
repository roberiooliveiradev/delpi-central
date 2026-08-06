"""Use cases — listagens process inspection plans."""

from __future__ import annotations

from app.application.use_cases.process_inspection_plans.get_process_inspection_plans_product_use_case import (
    GetProcessInspectionPlansProductUseCase,
)
from app.application.use_cases.process_inspection_plans.list_process_inspection_plans_orders_without_plan_use_case import (
    ListProcessInspectionPlansOrdersWithoutPlanUseCase,
)
from app.application.use_cases.process_inspection_plans.list_process_inspection_plans_products_use_case import (
    ListProcessInspectionPlansProductsUseCase,
)
from app.application.use_cases.process_inspection_plans.list_process_inspection_plans_products_without_plan_use_case import (
    ListProcessInspectionPlansProductsWithoutPlanUseCase,
)


class _FakePlansRepo:
    def count_orders_without_plan(self, branch_scope: str) -> int:
        return 1

    def list_orders_without_plan(self, branch_scope: str, *, page: int, page_size: int):
        assert branch_scope == "01"
        assert page == 1
        return [
            {
                "branch": "01",
                "product_code": "8001",
                "product_description": "Desc",
                "production_order": "OP1",
                "observation": "obs",
            }
        ]

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

    def product_has_plan(self, product_code: str) -> bool:
        return product_code == "8001"


class _FakeInspection:
    def __init__(self):
        self.product_code = "8001"
        self.bom_level = 0
        self.has_inspection = True
        self.header = {"revision": "001"}
        self.measurable_tests = []
        self.textual_tests = []


class _FakeInspectionRepo:
    def fetch_inspection_rows(self, code: str, max_depth: int):
        assert code == "8001"
        assert max_depth == 0
        return [_FakeInspection()]


def test_list_orders_without_plan_use_case() -> None:
    uc = ListProcessInspectionPlansOrdersWithoutPlanUseCase(repository=_FakePlansRepo())
    data = uc.execute(branch="01", page=1, page_size=50).to_dict()
    assert data["items"][0]["production_order"] == "OP1"
    assert data["pagination"]["total"] == 1


def test_list_products_without_plan_use_case() -> None:
    uc = ListProcessInspectionPlansProductsWithoutPlanUseCase(repository=_FakePlansRepo())
    data = uc.execute(branch="01", page=1, page_size=50).to_dict()
    assert data["items"][0]["open_orders_count"] == 2


def test_list_products_with_plan_use_case() -> None:
    uc = ListProcessInspectionPlansProductsUseCase(repository=_FakePlansRepo())
    data = uc.execute(page=1, page_size=50).to_dict()
    assert data["items"][0]["revision"] == "001"


def test_get_product_plan_use_case() -> None:
    uc = GetProcessInspectionPlansProductUseCase(
        plans_repository=_FakePlansRepo(),
        inspection_repository=_FakeInspectionRepo(),
    )
    data = uc.execute(product_code="8001", include_bom=False)
    assert data is not None
    assert data.to_dict()["total"] == 1
    assert uc.execute(product_code="MISSING") is None
