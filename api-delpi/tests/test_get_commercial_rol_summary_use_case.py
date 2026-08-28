"""Unit — GetCommercialRolSummaryUseCase."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.application.use_cases.commercial.get_commercial_rol_summary_use_case import (
    GetCommercialRolSummaryUseCase,
)


def test_commercial_rol_summary_maps_rol_and_treats_branch_all_as_consolidated() -> None:
    financial = MagicMock()
    financial.get_rol.return_value = {
        "rol": 1500.5,
        "gross_revenue": 2000.0,
        "returns": 100.0,
        "discounts": 50.0,
    }
    use_case = GetCommercialRolSummaryUseCase(financial_query_repository=financial)
    result = use_case.execute(
        branch="all",
        start_date="2026-08-01",
        end_date="2026-08-28",
        customer_codes=["000001"],
    )
    assert result["branch"] is None
    assert result["rol"] == 1500.5
    assert result["gross_revenue"] == 2000.0
    request = financial.get_rol.call_args.args[0]
    assert request.branch is None
    assert request.customer_codes == ["000001"]
    assert request.start_date == "2026-08-01"


def test_commercial_rol_summary_keeps_concrete_branch() -> None:
    financial = MagicMock()
    financial.get_rol.return_value = {"rol": 10, "gross_revenue": 0, "returns": 0, "discounts": 0}
    use_case = GetCommercialRolSummaryUseCase(financial_query_repository=financial)
    result = use_case.execute(branch="01", start_date="20260801", end_date="20260828")
    assert result["branch"] == "01"
    assert result["start_date"] == "2026-08-01"
    assert financial.get_rol.call_args.args[0].branch == "01"
