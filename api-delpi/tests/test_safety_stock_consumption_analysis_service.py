from __future__ import annotations

from datetime import date

from app.domain.services.supplies.safety_stock_consumption_analysis_service import (
    ANALYSIS_CALENDAR_DAYS,
    STATUS_ABOVE,
    STATUS_ADEQUATE,
    STATUS_BELOW,
    STATUS_INCONSISTENT,
    SafetyStockConsumptionAnalysisService,
)


def test_resolve_period_is_inclusive_365_days() -> None:
    start, end, business_days = SafetyStockConsumptionAnalysisService.resolve_period(
        as_of=date(2026, 7, 17)
    )
    assert end == date(2026, 7, 17)
    assert start == date(2025, 7, 18)
    assert (end - start).days + 1 == ANALYSIS_CALENDAR_DAYS
    assert business_days > 0


def test_resolve_annual_comparison_period_covers_three_calendar_years() -> None:
    start, end, years = (
        SafetyStockConsumptionAnalysisService.resolve_annual_comparison_period(
            as_of=date(2026, 7, 17)
        )
    )
    assert start == date(2024, 1, 1)
    assert end == date(2026, 7, 17)
    assert years == [2024, 2025, 2026]


def test_build_annual_comparison_pivots_month_by_year() -> None:
    comparison = SafetyStockConsumptionAnalysisService.build_annual_comparison(
        [
            {
                "year_month": "202401",
                "consumption_quantity": 10,
            },
            {
                "year_month": "202501",
                "consumption_quantity": 20,
            },
            {
                "year_month": "202607",
                "consumption_quantity": 30,
            },
        ],
        years=[2024, 2025, 2026],
        period_start=date(2024, 1, 1),
        period_end=date(2026, 7, 17),
    )
    assert comparison["years"] == ["2024", "2025", "2026"]
    january = comparison["items"][0]
    assert january["month_label"] == "Jan"
    assert january["values_by_year"]["2024"] == 10.0
    assert january["values_by_year"]["2025"] == 20.0
    assert january["values_by_year"]["2026"] == 0.0
    august = comparison["items"][7]
    assert august["values_by_year"]["2026"] is None
    july = comparison["items"][6]
    assert july["values_by_year"]["2026"] == 30.0


def test_average_daily_consumption() -> None:
    assert (
        SafetyStockConsumptionAnalysisService.average_daily_consumption(
            period_consumption=13000,
            period_business_days=130,
        )
        == 100.0
    )


def test_suggested_safety_stock_ceils_and_never_negative() -> None:
    suggested = SafetyStockConsumptionAnalysisService.suggested_safety_stock(
        average_daily_consumption=10.1,
        lead_time_business_days=5,
    )
    assert suggested == 51.0
    assert (
        SafetyStockConsumptionAnalysisService.suggested_safety_stock(
            average_daily_consumption=-5,
            lead_time_business_days=3,
        )
        == 0.0
    )


def test_lead_time_zero_marks_inconsistent() -> None:
    status = SafetyStockConsumptionAnalysisService.classify_suggestion_status(
        current_safety_stock=100,
        suggested_safety_stock=0,
        period_consumption=100,
        lead_time_calendar_days=0,
        average_daily_consumption=10,
    )
    assert status == STATUS_INCONSISTENT


def test_classify_below_above_adequate() -> None:
    assert (
        SafetyStockConsumptionAnalysisService.classify_suggestion_status(
            current_safety_stock=80,
            suggested_safety_stock=100,
            period_consumption=1000,
            lead_time_calendar_days=10,
            average_daily_consumption=10,
        )
        == STATUS_BELOW
    )
    assert (
        SafetyStockConsumptionAnalysisService.classify_suggestion_status(
            current_safety_stock=120,
            suggested_safety_stock=100,
            period_consumption=1000,
            lead_time_calendar_days=10,
            average_daily_consumption=10,
        )
        == STATUS_ABOVE
    )
    assert (
        SafetyStockConsumptionAnalysisService.classify_suggestion_status(
            current_safety_stock=102,
            suggested_safety_stock=100,
            period_consumption=1000,
            lead_time_calendar_days=10,
            average_daily_consumption=10,
        )
        == STATUS_ADEQUATE
    )


def test_enrich_row_builds_managerial_fields() -> None:
    period_start = date(2025, 7, 18)
    period_end = date(2026, 7, 17)
    enriched = SafetyStockConsumptionAnalysisService.enrich_row(
        {
            "product_code": "10020113",
            "safety_stock": 80,
            "lead_time_days": 10,
            "available_stock": 200,
            "period_consumption": 1300,
            "primary_stock": 100,
            "warehouse_98_stock": 50,
            "warehouse_99_stock": 50,
        },
        period_start=period_start,
        period_end=period_end,
        period_business_days=130,
        as_of=period_end,
    )
    assert enriched["average_daily_consumption"] == 10.0
    assert enriched["suggested_safety_stock"] > 0
    assert enriched["coverage_business_days"] == 20.0
    assert enriched["analysis_status"] in {
        STATUS_BELOW,
        STATUS_ABOVE,
        STATUS_ADEQUATE,
        STATUS_INCONSISTENT,
    }
    memory = SafetyStockConsumptionAnalysisService.build_calculation_memory(enriched)
    assert "ceil" in memory["formula"]
    assert memory["current_safety_stock"] == 80
