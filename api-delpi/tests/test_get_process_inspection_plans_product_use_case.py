"""Use case — process inspection plan product detail."""

from __future__ import annotations

from app.application.use_cases.process_inspection_plans.get_process_inspection_plans_product_use_case import (
    GetProcessInspectionPlansProductUseCase,
)


class _FakePlansRepo:
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
        assert max_depth == 0
        return [_FakeInspection()]


def test_get_product_plan_detail_use_case() -> None:
    uc = GetProcessInspectionPlansProductUseCase(
        plans_repository=_FakePlansRepo(),
        inspection_repository=_FakeInspectionRepo(),
    )
    data = uc.execute(product_code="8001", include_bom=False)
    assert data is not None
    assert data.to_dict()["total"] == 1
    assert uc.execute(product_code="MISSING") is None
