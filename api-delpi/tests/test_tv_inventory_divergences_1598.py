"""GLPI #1598: contratos do painel TV sem consultas reais ao SQL Server."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.application.services.supplies.inventory_adjustments_tv_service import (
    InventoryAdjustmentsTvService,
    _filters,
    _reference_date,
    _selected_period,
    _bucket_range,
)
from app.infrastructure.persistence.totvs.supplies_repositories.inventory_adjustments_tv_repository import (
    InventoryAdjustmentsTvRepository,
)


class FakeSummary:
    def __init__(self):
        self.requests = []

    def execute(self, request):
        self.requests.append(request)
        return {
            "period_start": "2025-01-01",
            "period_end": "2025-11-19",
            "summary": {
                "gross_value": 175, "shortage_value": 125,
                "surplus_value": 50, "net_value": -75,
                "adjustment_count": 5, "shortage_count": 3, "surplus_count": 2,
            },
            "by_month": [
                {
                    "month": "2025-01", "gross_value": 100, "shortage_value": 80,
                    "surplus_value": 20, "net_value": -60,
                    "adjustment_count": 3, "shortage_count": 2, "surplus_count": 1,
                },
                {
                    "month": "2025-11", "gross_value": 75, "shortage_value": 45,
                    "surplus_value": 30, "net_value": -15,
                    "adjustment_count": 2, "shortage_count": 1, "surplus_count": 1,
                },
            ],
        }


class FakeWeekly:
    def __init__(self):
        self.args = None

    def fetch_weekly_product_divergences(self, **kwargs):
        self.args = kwargs
        return {"items": [{"product_code": "P001", "nature": "shortage", "value_brl": 50}],
                "total_groups": 26, "returned": 1, "truncated": True}


def service():
    summary, weekly = FakeSummary(), FakeWeekly()
    return InventoryAdjustmentsTvService(
        summary_use_case=summary, weekly_repository=weekly
    ), summary, weekly


def test_summary_reuses_owner_summary_and_does_not_net_shortages_with_surpluses():
    subject, summary, _ = service()
    response = subject.summary(as_of="2025-11-19", branch="02", warehouse="01")
    assert response["year_divergence_brl"] == 175
    assert response["month_divergence_brl"] == 75
    assert response["year_shortage_value_brl"] == 125
    assert response["year_surplus_value_brl"] == 50
    assert response["year_net_value_brl"] == -75
    assert response["month_net_value_brl"] == -15
    assert response["divergence_definition"] == "gross_shortages_plus_surpluses"
    assert len(summary.requests) == 1
    assert summary.requests[0].start_date == "2025-01-01"
    assert summary.requests[0].end_date == "2025-11-19"
    assert summary.requests[0].branch == "02"
    assert summary.requests[0].warehouse == "01"


def test_monthly_series_is_calendar_month_aligned_with_zero_fill():
    subject, _, _ = service()
    result = subject.monthly_series(as_of="2025-11-19", branch="01")
    assert len(result["items"]) == 11
    assert result["items"][0]["periodo"] == "2025-01"
    assert result["items"][0]["gross_value_brl"] == 100
    assert result["items"][1]["periodo"] == "2025-02"
    assert result["items"][1]["gross_value_brl"] == 0
    assert result["items"][-1]["periodo"] == "2025-11"
    assert result["items"][-1]["shortage_value_brl"] == 45
    assert result["items"][-1]["surplus_value_brl"] == 30


def test_weekly_uses_iso_monday_to_reference_and_bounded_top_n():
    subject, _, weekly = service()
    payload = subject.weekly_items(
        as_of="2025-11-19", branch="02", warehouse="99", top_limit=10,
    )
    assert payload["week_start"] == "2025-11-17"
    assert payload["week_end"] == "2025-11-19"
    assert payload["item_grain"] == "branch_product"
    assert payload["total_groups"] == 26
    assert payload["truncated"] is True
    assert weekly.args == {
        "date_start": "20251117", "date_end_exclusive": "20251120",
        "branch": "02", "warehouse": "99", "top_limit": 10,
    }


def test_bad_filters_and_future_dates_fail_closed():
    with pytest.raises(ValueError):
        _filters("03", None)
    with pytest.raises(ValueError):
        _filters("02", "??")
    with pytest.raises(ValueError):
        _reference_date("2055-03-09")
    with pytest.raises(ValueError):
        _reference_date("2026-13-70")


class FakeSqlRepository(InventoryAdjustmentsTvRepository):
    def __init__(self):
        self.sql = None
        self.params = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute_query(self, sql, params):
        self.sql, self.params = sql, params
        return [{
            "branch": "02", "product_code": "P001",
            "product_description": "Cabo", "unit": "M",
            "movement_count": 2, "warehouse_count": 2,
            "shortage_count": 1, "surplus_count": 1,
            "signed_quantity": "-5.500000", "signed_value": "-14.335000",
            "unpriced_movements": 0, "total_groups": 18,
        }]


def test_weekly_sql_aggregates_all_movements_before_top_ranking():
    subject = FakeSqlRepository()
    data = subject.fetch_weekly_product_divergences(
        date_start="20251117", date_end_exclusive="20251120",
        branch="02", warehouse="01", top_limit=10,
    )
    sql = subject.sql
    assert sql is not None
    assert "RTRIM(LTRIM(SD3.D3_DOC)) = 'INVENT'" in sql
    assert "SD3.D3_ESTORNO" in sql
    assert "SD3.D3_CUSTO1" in sql
    assert "COUNT(*) OVER () AS total_groups" in sql
    assert "GROUP BY RTRIM(SD3.D3_FILIAL), RTRIM(SD3.D3_COD)" in sql
    assert "GROUP BY SD3.D3_FILIAL, SD3.D3_COD, SD3.D3_LOCAL" not in sql
    assert "COUNT(DISTINCT RTRIM(SD3.D3_LOCAL))" in sql
    assert "S.B1_COD = A.product_code" in sql
    assert "RE0" in sql and "DE0" in sql
    assert sql.index("WITH AGG") < sql.index("SELECT TOP (?)")
    assert "ORDER BY ABS(A.signed_value) DESC" in sql
    assert subject.params[-1] == 10
    assert data["items"][0]["quantity"] == 5.5
    assert data["items"][0]["warehouse_count"] == 2
    assert data["items"][0]["warehouse"] == "01"
    assert data["items"][0]["nature_label"] == "Falta"
    assert data["items"][0]["signed_quantity"] == -5.5
    assert data["items"][0]["value_brl"] == 14.34
    assert data["items"][0]["signed_value_brl"] == -14.34
    assert data["truncated"] is True
    assert data["total_groups"] == 18


def test_routes_stay_read_only_and_reuse_existing_permission_gate():
    router = (
        Path(__file__).resolve().parents[1]
        / "app/interface/http/routes/supplies/inventory_adjustments_router.py"
    ).read_text(encoding="utf-8")
    for suffix in ("/tv/summary", "/tv/monthly-series", "/tv/weekly-items"):
        assert f'"{suffix}"' in router
    assert router.count("@require_permission(API_DELPI_ACCESS)") >= 5


# ── GLPI #1598 | seleção de período e granularidade para TV ──────────────


def test_default_summary_has_period_card_and_keeps_old_year_month_fields():
    subject, summary, _ = service()
    result = subject.summary(as_of="2025-11-19", granularity="month", branch="02")
    assert result["period_start"] == "2025-11-01"
    assert result["period_end"] == "2025-11-19"
    assert result["granularity"] == "month"
    assert result["year_divergence_brl"] == 175
    assert result["month_divergence_brl"] == 75
    assert result["period_divergence_brl"] == 75
    assert len(summary.requests) == 1


def test_summary_week_uses_monday_and_preserves_legacy_totals():
    subject, summary, _ = service()
    result = subject.summary(as_of="2025-11-19", granularity="week")
    assert result["period_start"] == "2025-11-17"
    assert result["period_end"] == "2025-11-19"
    assert result["year_divergence_brl"] == 175
    assert result["month_divergence_brl"] == 75
    assert result["period_divergence_brl"] == 175  # resposta fake de teste
    assert len(summary.requests) == 2
    assert summary.requests[1].start_date == "2025-11-17"
    assert summary.requests[1].end_date == "2025-11-19"


def test_period_keys_follow_day_week_month_year_with_historical_reference():
    examples = (
        ("day", "2025-11-19"),
        ("week", "2025-11-17"),
        ("month", "2025-11-01"),
        ("year", "2025-01-01"),
    )
    for granularity, expected_start in examples:
        result = _selected_period(
            granularity=granularity, as_of="2025-11-19", start_date=None,
            end_date=None, default_window="granularity",
        )
        assert result.start.isoformat() == expected_start
        assert result.end.isoformat() == "2025-11-19"


def test_custom_tv_week_preset_overrides_granularity_default_for_top_items():
    subject, _, weekly = service()
    result = subject.weekly_items(
        granularity="month", start_date="2025-11-17", end_date="2025-11-19",
        branch="02", top_limit=5,
    )
    assert result["granularity"] == "month"
    assert result["period_start"] == "2025-11-17"
    assert result["period_end"] == "2025-11-19"
    assert weekly.args["date_start"] == "20251117"
    assert weekly.args["date_end_exclusive"] == "20251120"
    assert weekly.args["top_limit"] == 5
    assert result["week_start"] is None


def test_top_items_granularity_month_without_date_range_uses_mtd():
    subject, _, weekly = service()
    result = subject.weekly_items(as_of="2025-11-19", granularity="month")
    assert weekly.args["date_start"] == "20251101"
    assert weekly.args["date_end_exclusive"] == "20251120"
    assert result["period_start"] == "2025-11-01"


def test_custom_date_range_end_is_inclusive_and_historical_as_of_is_inferred():
    period = _selected_period(
        granularity="month", as_of=None,
        start_date="2025-10-01", end_date="2025-10-31",
        default_window="year",
    )
    assert period.reference.isoformat() == "2025-10-31"
    assert period.start.isoformat() == "2025-10-01"
    assert period.end.isoformat() == "2025-10-31"


def test_full_calendar_future_end_is_capped_to_as_of_and_is_not_future_data():
    period = _selected_period(
        granularity="day", as_of="2025-11-19",
        start_date="2025-11-01", end_date="2025-11-30",
        default_window="granularity",
    )
    assert period.start.isoformat() == "2025-11-01"
    assert period.end.isoformat() == "2025-11-19"


def test_invalid_granularity_partial_dates_inverted_period_and_oversized_range():
    common = dict(as_of="2025-11-19", default_window="year")
    for params in (
        dict(granularity="quarter", start_date=None, end_date=None),
        dict(granularity="month", start_date="2025-11-01", end_date=None),
        dict(granularity="month", start_date="2025-11-19", end_date="2025-11-01"),
        dict(granularity="month", start_date="2024-01-01", end_date="2025-11-19"),
    ):
        with pytest.raises(ValueError):
            _selected_period(**common, **params)


def test_bucket_range_respects_monday_year_crossover_and_month_zero_fill():
    week_period = _selected_period(
        granularity="week", as_of="2025-01-08",
        start_date="2024-12-30", end_date="2025-01-08",
        default_window="year",
    )
    assert _bucket_range(week_period) == ["2024-12-30", "2025-01-06"]
    month_period = _selected_period(
        granularity="month", as_of="2025-02-03",
        start_date="2024-12-30", end_date="2025-02-03",
        default_window="year",
    )
    assert _bucket_range(month_period) == ["2024-12", "2025-01", "2025-02"]


def test_day_series_uses_real_daily_buckets_not_monthly_proration():
    class DailyRows(FakeWeekly):
        def fetch_granular_series(self, **kwargs):
            self.args = kwargs
            return [{
                "bucket": "20251118", "gross_value": 90,
                "shortage_value": 75, "surplus_value": 15,
                "net_value": -60, "adjustment_count": 2,
                "shortage_count": 1, "surplus_count": 1,
            }]

    daily = DailyRows()
    subject = InventoryAdjustmentsTvService(
        summary_use_case=FakeSummary(), weekly_repository=daily,
    )
    result = subject.monthly_series(
        granularity="day", start_date="2025-11-17", end_date="2025-11-19",
    )
    assert result["granularity"] == "day"
    assert [x["periodo"] for x in result["items"]] == [
        "2025-11-17", "2025-11-18", "2025-11-19",
    ]
    assert [x["gross_value_brl"] for x in result["items"]] == [0, 90, 0]
    assert daily.args["date_start"] == "20251117"
    assert daily.args["date_end_exclusive"] == "20251120"


def test_weekly_series_uses_iso_week_bucket_and_zero_fills():
    class WeeklyRows(FakeWeekly):
        def fetch_granular_series(self, **kwargs):
            self.args = kwargs
            return [{
                "bucket": "20241230", "gross_value": 150,
                "shortage_value": 100, "surplus_value": 50,
                "net_value": -50,
                "adjustment_count": 2, "shortage_count": 1, "surplus_count": 1,
            }]

    source = WeeklyRows()
    subject = InventoryAdjustmentsTvService(
        summary_use_case=FakeSummary(), weekly_repository=source,
    )
    result = subject.monthly_series(
        granularity="week", start_date="2024-12-30", end_date="2025-01-08",
    )
    assert result["granularity"] == "week"
    assert [x["periodo"] for x in result["items"]] == [
        "2024-12-30", "2025-01-06",
    ]
    assert result["items"][0]["gross_value_brl"] == 150
    assert result["items"][1]["gross_value_brl"] == 0
    assert source.args["granularity"] == "week"


def test_monthly_series_custom_period_does_not_assume_full_year():
    subject, summary, _ = service()
    result = subject.monthly_series(
        granularity="month", start_date="2025-10-01", end_date="2025-11-19",
    )
    assert result["period_start"] == "2025-10-01"
    assert result["period_end"] == "2025-11-19"
    assert [x["periodo"] for x in result["items"]] == ["2025-10", "2025-11"]
    assert result["items"][0]["gross_value_brl"] == 0
    assert result["items"][1]["gross_value_brl"] == 75
    assert summary.requests[0].start_date == "2025-10-01"


def test_year_series_groups_existing_month_rows_without_losing_totals():
    subject, _, _ = service()
    result = subject.monthly_series(
        granularity="year", as_of="2025-11-19",
    )
    assert len(result["items"]) == 1
    assert result["items"][0]["periodo"] == "2025"
    assert result["items"][0]["gross_value_brl"] == 175
    assert result["items"][0]["shortage_value_brl"] == 125


def test_sql_bucket_validation_fail_closed_and_week_ignores_datefirst():
    class SeriesRepo(FakeSqlRepository):
        def execute_query(self, sql, params):
            self.sql, self.params = sql, params
            return [{
                "bucket": "20241230",
                "gross_adjustment_value": 90,
                "net_adjustment_value": -50,
                "shortage_value": 70,
                "surplus_value": 20,
                "adjustment_count": 3,
                "shortage_count": 2,
                "surplus_count": 1,
            }]

    repo = SeriesRepo()
    with pytest.raises(ValueError):
        repo.fetch_granular_series(
            date_start="20241230", date_end_exclusive="20250109",
            branch="02", warehouse=None, granularity="invalid",
        )
    assert repo.sql is None
    result = repo.fetch_granular_series(
        date_start="20241230", date_end_exclusive="20250109",
        branch="02", warehouse=None, granularity="week",
    )
    assert "DATEFROMPARTS(1900, 1, 1)" in repo.sql
    assert "DATEFIRST" not in repo.sql
    assert "D3_DOC" in repo.sql and "D3_ESTORNO" in repo.sql
    assert "GROUP BY" in repo.sql
    assert result[0]["bucket"] == "20241230"
    assert result[0]["gross_value"] == 90


def test_openapi_exposes_granularity_and_standard_date_range_on_all_three_routes():
    from app.main import app

    paths = app.openapi()["paths"]
    expectations = (
        ("/tv/summary", "month"),
        ("/tv/monthly-series", "month"),
        ("/tv/weekly-items", "week"),
    )
    for suffix, default in expectations:
        item = paths["/supplies/inventory-adjustments" + suffix]["get"]
        parameters = {p["name"]: p for p in item["parameters"]}
        assert {"granularity", "start_date", "end_date", "branch"}.issubset(parameters)
        granularity = parameters["granularity"]["schema"]
        assert granularity["default"] == default
        assert granularity["enum"] == ["day", "week", "month", "year"]
