"""GLPI #1598: contratos do painel TV sem consultas reais ao SQL Server."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.application.services.supplies.inventory_adjustments_tv_service import (
    InventoryAdjustmentsTvService,
    _filters,
    _reference_date,
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
            "branch": "02", "product_code": "P001", "warehouse": "01",
            "product_description": "Cabo", "unit": "M",
            "nature": "shortage", "movement_count": 2,
            "quantity": "5.500000", "signed_quantity": "-5.500000",
            "gross_value": "14.335000", "signed_value": "-14.335000",
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
    assert "GROUP BY" in sql and "SD3.D3_LOCAL" in sql
    assert "S.B1_COD = A.product_code" in sql
    assert "RE0" in sql and "DE0" in sql
    assert sql.index("WITH AGG") < sql.index("SELECT TOP (?)")
    assert subject.params[-1] == 10
    assert data["items"][0]["quantity"] == 5.5
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
