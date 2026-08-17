"""Use case — process inspection plans summary."""

from __future__ import annotations

from app.application.use_cases.process_inspection_plans.get_process_inspection_plans_summary_use_case import (
    GetProcessInspectionPlansSummaryUseCase,
)


class _FakeRepo:
    def get_summary(self, branch_scope: str) -> dict:
        assert branch_scope == "01"
        return {
            "total_open_orders": 100,
            "orders_without_plan": 25,
            "products_without_plan": 10,
            "orders_with_plan": 75,
        }


def test_summary_use_case_builds_distribution() -> None:
    uc = GetProcessInspectionPlansSummaryUseCase(repository=_FakeRepo())
    result = uc.execute(branch="01").to_dict()
    assert result["registered_pct"] == 75.0
    assert result["orders_without_plan"] == 25
    assert result["products_without_plan"] == 10
    assert result["distribution"][0]["status"] == "with_plan"
    assert result["distribution"][0]["label"] == "Com inspeção"
    assert result["distribution"][0]["count"] == 75
    assert result["distribution"][1]["status"] == "without_plan"
    assert result["distribution"][1]["label"] == "Sem inspeção"
    assert result["distribution"][1]["count"] == 25
