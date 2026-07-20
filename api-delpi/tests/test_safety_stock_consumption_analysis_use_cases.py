from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

from app.application.dto.supplies.safety_stock_request import (
    SafetyStockConsumptionAnalysisItemsRequest,
    SafetyStockConsumptionAnalysisQueryRequest,
    SafetyStockItemDetailsRequest,
)
from app.application.use_cases.supplies.get_safety_stock_consumption_analysis_item_details_use_case import (
    GetSafetyStockConsumptionAnalysisItemDetailsUseCase,
)
from app.application.use_cases.supplies.get_safety_stock_consumption_analysis_items_use_case import (
    GetSafetyStockConsumptionAnalysisItemsUseCase,
)
from app.application.use_cases.supplies.get_safety_stock_consumption_analysis_summary_use_case import (
    GetSafetyStockConsumptionAnalysisSummaryUseCase,
)


def _raw_row(**overrides):
    base = {
        "product_code": "10020113",
        "product_description": "Material",
        "product_type": "MP",
        "unit": "PC",
        "product_group": "GRP",
        "branch": "01",
        "blocked": False,
        "safety_stock": 50,
        "lead_time_days": 10,
        "primary_stock": 20,
        "work_in_process_stock": 0,
        "warehouse_50_stock": 0,
        "warehouse_98_stock": 0,
        "warehouse_99_stock": 10,
        "available_stock": 30,
        "work_in_process_committed": 0,
        "work_in_process_available": 0,
        "deficit_quantity": 20,
        "status": "below_safety_stock",
        "period_consumption": 1300,
        "movement_count": 5,
        "first_movement_date": "2025-08-01",
        "last_movement_date": "2026-07-01",
    }
    base.update(overrides)
    return base


@patch(
    "app.application.services.supplies.safety_stock_consumption_analysis_query_service."
    "get_cached_consumption_analysis",
    return_value=None,
)
@patch(
    "app.application.services.supplies.safety_stock_consumption_analysis_query_service."
    "set_cached_consumption_analysis"
)
def test_summary_and_items_use_cases(_set_cache, _get_cache) -> None:
    repo = MagicMock()
    repo.fetch_consumption_analysis_rows.return_value = [
        _raw_row(product_code="A", safety_stock=10),
        _raw_row(product_code="B", safety_stock=500, period_consumption=100),
    ]

    summary_uc = GetSafetyStockConsumptionAnalysisSummaryUseCase(repo)
    summary = summary_uc.execute(
        SafetyStockConsumptionAnalysisQueryRequest(branch="01")
    )
    assert summary["analyzed_items"] == 2
    assert summary["period_calendar_days"] == 365
    assert "status_distribution" in summary

    items_uc = GetSafetyStockConsumptionAnalysisItemsUseCase(repo)
    page = items_uc.execute(
        SafetyStockConsumptionAnalysisItemsRequest(
            branch="01",
            page=1,
            page_size=1,
            sort_by="product_code",
            sort_direction="asc",
        )
    )
    assert page["total"] == 2
    assert page["total_pages"] == 2
    assert len(page["items"]) == 1
    assert page["items"][0]["product_code"] == "A"


def test_item_details_use_case_returns_memory_and_series() -> None:
    repo = MagicMock()
    repo.fetch_consumption_analysis_rows.return_value = [_raw_row()]
    repo.fetch_consumption_monthly_series.return_value = [
        {
            "year_month": "202607",
            "year_month_label": "2026-07",
            "consumption_quantity": 100,
            "movement_count": 2,
        }
    ]

    result = GetSafetyStockConsumptionAnalysisItemDetailsUseCase(repo).execute(
        SafetyStockItemDetailsRequest(branch="01", product_code="10020113")
    )
    assert result is not None
    assert result["item"]["product_code"] == "10020113"
    assert result["monthly_consumption"]["total"] == 1
    assert "annual_comparison" in result
    assert result["annual_comparison"]["years"]
    assert "formula" in result["calculation_memory"]
    repo.fetch_consumption_monthly_series.assert_called_once()
    annual_start = repo.fetch_consumption_monthly_series.call_args.kwargs["period_start"]
    assert str(annual_start).endswith("0101")
