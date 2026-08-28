from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from typing import Any

from production_control_app.application.services.overview_service import OverviewService
from production_control_app.domain.services.branch_access_service import BranchAccessService
from production_control_app.domain.services.current_month_period import current_month_bounds
from production_control_app.domain.services.product_code_scope import product_code_matches_prefixes


class FakeGateway:
    def __init__(self, items: list[dict[str, Any]] | None = None) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.items = items or [
            {
                "production_order": "OP001",
                "op_key": "01|OP001",
                "product_code": "9001234",
                "product_description": "Transformador A",
                "days_late": 5,
                "planned_qty": 10,
                "produced_qty": 4,
                "pending_qty": 6,
                "branch": "01",
            }
        ]

    def fetch_pcp_orders_summary(self, *, branch: str) -> dict[str, Any]:
        self.calls.append(("summary", {"branch": branch}))
        return {"success": True, "data": {"summary": {"open_orders": 40, "delayed_orders": len(self.items)}}}

    def fetch_pcp_orders_items(
        self,
        *,
        branch: str,
        delayed_only: bool,
        page_size: int,
    ) -> dict[str, Any]:
        self.calls.append(
            ("items", {"branch": branch, "delayed_only": delayed_only, "page_size": page_size})
        )
        return {
            "success": True,
            "data": {
                "items": [
                    {**item, "branch": item.get("branch") or branch} for item in self.items
                ]
            },
        }

    def fetch_production_otd(
        self,
        *,
        branch: str,
        start_date: str,
        end_date: str,
        page_size: int,
    ) -> dict[str, Any]:
        self.calls.append(
            (
                "otd",
                {
                    "branch": branch,
                    "start_date": start_date,
                    "end_date": end_date,
                    "page_size": page_size,
                },
            )
        )
        return {
            "success": True,
            "data": {
                "summary": {
                    "total_ops_finished": 100,
                    "on_time_ops": 97,
                    "late_ops": 3,
                    "on_time_delivery_pct": 97.0,
                    "late_percentage": 3.0,
                }
            },
        }

    def fetch_production_otd_series(
        self,
        *,
        branch: str,
        start_date: str,
        end_date: str,
        granularity: str,
    ) -> dict[str, Any]:
        self.calls.append(
            (
                "otd_series",
                {
                    "branch": branch,
                    "start_date": start_date,
                    "end_date": end_date,
                    "granularity": granularity,
                },
            )
        )
        return {
            "success": True,
            "data": {
                "points": [
                    {
                        "periodo": "01/08",
                        "start_date": "2026-08-01",
                        "end_date": "2026-08-01",
                        "otd_filial_01": 96.5,
                        "otd_filial_02": 88.0,
                    },
                    {
                        "periodo": "02/08",
                        "start_date": "2026-08-02",
                        "end_date": "2026-08-02",
                        "otd_filial_01": 97.91,
                        "otd_filial_02": 90.0,
                    },
                ]
            },
        }

    def fetch_production_appointments_series(
        self,
        *,
        branch: str,
        start_date: str,
        end_date: str,
        granularity: str,
    ) -> dict[str, Any]:
        self.calls.append(
            (
                "appointments_series",
                {
                    "branch": branch,
                    "start_date": start_date,
                    "end_date": end_date,
                    "granularity": granularity,
                },
            )
        )
        if granularity == "month":
            year = int(start_date[:4])
            # Ano corrente: jan–ago com volumes; ano anterior: volumes menores.
            scale = 1.0 if year >= 2026 else 0.8
            points = []
            for month in range(1, 9):
                points.append(
                    {
                        "periodo": f"{year}-{month:02d}",
                        "start_date": f"{year}-{month:02d}-01",
                        "end_date": f"{year}-{month:02d}-28",
                        "qty_produced": round(100.0 * month * scale, 1),
                        "qty_lost": 0.0,
                    }
                )
            return {"success": True, "data": {"points": points}}

        return {
            "success": True,
            "data": {
                "points": [
                    {
                        "periodo": "2026-08-01",
                        "appointment_date": "2026-08-01",
                        "start_date": "2026-08-01",
                        "end_date": "2026-08-01",
                        "qty_produced": 50.0,
                        "qty_lost": 3.0,
                    },
                    {
                        "periodo": "2026-08-02",
                        "appointment_date": "2026-08-02",
                        "start_date": "2026-08-02",
                        "end_date": "2026-08-02",
                        "qty_produced": 40.0,
                        "qty_lost": 1.5,
                    },
                    {
                        "periodo": "2026-08-03",
                        "appointment_date": "2026-08-03",
                        "start_date": "2026-08-03",
                        "end_date": "2026-08-03",
                        "qty_produced": 100.0,
                        "qty_lost": 0.0,
                    },
                    {
                        "periodo": "2026-08-04",
                        "appointment_date": "2026-08-04",
                        "start_date": "2026-08-04",
                        "end_date": "2026-08-04",
                        "qty_produced": 120.0,
                        "qty_lost": 0.0,
                    },
                ]
            },
        }

    def fetch_open_sales_orders(self) -> dict[str, Any]:
        self.calls.append(("open_sales", {}))
        return {"success": True, "data": {"items": []}}

    def fetch_recently_closed_orders(self, *, days: int) -> dict[str, Any]:
        self.calls.append(("recently_closed", {"days": days}))
        return {"success": True, "data": {"items": []}}


def _user(*permissions: str):
    return SimpleNamespace(is_superadmin=False, permissions=list(permissions))


FULL_PERMS = (
    "production-control.access",
    "production-control.problem-analysis.view",
    "production-control.view.filial-01",
    "production-control.view.filial-02",
)


def test_current_month_bounds_uses_first_day_through_today() -> None:
    start, end = current_month_bounds(timezone="America/Sao_Paulo", today=date(2026, 8, 19))
    assert start.isoformat() == "2026-08-01"
    assert end.isoformat() == "2026-08-19"


def test_resolve_overview_period_uses_explicit_range_or_default() -> None:
    from production_control_app.domain.services.current_month_period import resolve_overview_period

    start, end = resolve_overview_period(
        timezone="America/Sao_Paulo",
        today=date(2026, 8, 28),
        start_date="2026-07-01",
        end_date="2026-07-15",
    )
    assert start.isoformat() == "2026-07-01"
    assert end.isoformat() == "2026-07-15"

    fallback_start, fallback_end = resolve_overview_period(
        timezone="America/Sao_Paulo",
        today=date(2026, 8, 28),
        start_date="2026-08-20",
        end_date="2026-08-10",
    )
    assert fallback_start.isoformat() == "2026-08-01"
    assert fallback_end.isoformat() == "2026-08-28"


def test_overview_honors_custom_period_for_otd_and_volume() -> None:
    gateway = FakeGateway()
    service = OverviewService(gateway, branch_access=BranchAccessService())
    payload = service.build(
        _user(*FULL_PERMS),
        branch="01",
        start_date="2026-07-01",
        end_date="2026-07-31",
    )

    assert payload["period"]["start_date"] == "2026-07-01"
    assert payload["period"]["end_date"] == "2026-07-31"
    otd_call = next(params for name, params in gateway.calls if name == "otd")
    assert otd_call["start_date"] == "2026-07-01"
    assert otd_call["end_date"] == "2026-07-31"
    volume_call = next(params for name, params in gateway.calls if name == "appointments_series")
    assert volume_call["start_date"] == "2026-07-01"
    assert volume_call["end_date"] == "2026-07-31"
    assert payload["production_volume"]["period"]["start_date"] == "2026-07-01"


def test_product_code_prefixes_8_and_9() -> None:
    assert product_code_matches_prefixes("90350341", ["8", "9"]) is True
    assert product_code_matches_prefixes("80012849", ["8", "9"]) is True
    assert product_code_matches_prefixes("50120001", ["8", "9"]) is False
    assert product_code_matches_prefixes(" 90263364", ["8", "9"]) is True
    assert product_code_matches_prefixes("", ["8", "9"]) is False


def test_overview_composes_otd_and_delayed_ops() -> None:
    gateway = FakeGateway()
    service = OverviewService(gateway, branch_access=BranchAccessService())
    payload = service.build(_user(*FULL_PERMS), branch="01")

    assert payload["branch"] == "01"
    assert payload["otd"]["on_time_delivery_pct"] == 97.0
    assert payload["otd"]["late_ops"] == 3
    assert payload["otd"]["series"][1]["value"] == 97.91
    assert payload["otd"]["series"][1]["label"] == "02/08"
    assert payload["delayed_ops"]["count"] == 1
    assert payload["delayed_ops"]["items"][0]["product_code"] == "9001234"
    assert payload["delayed_ops"]["items"][0]["metrics"]["pending_qty"] == 6.0
    assert payload["billing_due_today"]["line_count"] == 0
    assert payload["billing_due_today"]["customers"] == []

    kinds = {name for name, _ in gateway.calls}
    assert kinds == {
        "otd",
        "otd_series",
        "appointments_series",
        "items",
        "open_sales",
        "recently_closed",
    }
    series_call = next(params for name, params in gateway.calls if name == "otd_series")
    assert series_call["granularity"] == "day"
    assert series_call["branch"] == "01"
    closed_call = next(params for name, params in gateway.calls if name == "recently_closed")
    assert closed_call["days"] == 1
    assert payload["production_volume"]["total"] == 310.0
    assert payload["production_volume"]["view"] == "day"
    assert payload["production_volume"]["series"][0]["value"] == 50.0
    assert payload["production_volume"]["series"][0]["label"] == "01/08"
    # Perdida do apontamento não entra no volume do PCP.
    assert all("qty_lost" not in row for row in payload["production_volume"]["series"])
    # 01/08 e 02/08 são sábado/domingo — média só com 03 e 04 (100+120)/2.
    assert payload["production_volume"]["weekday_average"] == 110.0
    assert payload["production_volume"]["weekday_day_count"] == 2


def test_weekday_daily_average_ignores_weekend_points() -> None:
    from production_control_app.domain.services.weekday_daily_average import (
        is_weekend,
        weekday_daily_average,
    )

    assert is_weekend(date(2026, 8, 1)) is True
    assert is_weekend(date(2026, 8, 3)) is False
    result = weekday_daily_average(
        [
            {"start_date": "2026-08-01", "value": 999},
            {"start_date": "2026-08-03", "value": 10},
            {"start_date": "2026-08-04", "value": 30},
            {"start_date": None, "value": 50},
        ]
    )
    assert result["weekday_day_count"] == 2
    assert result["weekday_total"] == 40.0
    assert result["average"] == 20.0


def test_volume_view_month_yoy_merges_prior_year_by_month() -> None:
    from production_control_app.domain.services.volume_view import (
        build_month_yoy_series,
        parse_volume_view,
        shift_bounds_by_years,
        year_to_date_bounds,
    )

    assert parse_volume_view("month_yoy") == "month_yoy"
    assert parse_volume_view("nope") == "day"
    start, end = year_to_date_bounds(today=date(2026, 8, 21))
    assert start.isoformat() == "2026-01-01"
    assert end.isoformat() == "2026-08-21"
    prior_start, prior_end = shift_bounds_by_years(start, end, -1)
    assert prior_start.isoformat() == "2025-01-01"
    assert prior_end.isoformat() == "2025-08-21"

    rows = build_month_yoy_series(
        current_points=[
            {"start_date": "2026-01-01", "qty_produced": 10},
            {"start_date": "2026-03-01", "qty_produced": 30},
        ],
        prior_points=[
            {"periodo": "2025-01", "qty_produced": 8},
            {"periodo": "2025-03", "qty_produced": 20},
        ],
        year=2026,
        through_month=3,
    )
    assert [row["label"] for row in rows] == ["jan", "fev", "mar"]
    assert rows[0]["value"] == 10
    assert rows[0]["prior_value"] == 8
    assert rows[1]["value"] == 0
    assert rows[2]["prior_value"] == 20


def test_overview_month_yoy_fetches_two_month_series() -> None:
    gateway = FakeGateway()
    service = OverviewService(gateway, branch_access=BranchAccessService())
    payload = service.build(_user(*FULL_PERMS), branch="01", volume_view="month_yoy")
    volume = payload["production_volume"]
    assert volume["view"] == "month_yoy"
    assert volume["prior_year"] == volume["current_year"] - 1
    assert volume["series"][0]["label"] == "jan"
    assert "prior_value" in volume["series"][0]
    assert volume["prior_total"] is not None
    assert volume["weekday_average"] is None
    month_calls = [
        params
        for name, params in gateway.calls
        if name == "appointments_series" and params["granularity"] == "month"
    ]
    assert len(month_calls) == 2
    assert month_calls[0]["start_date"].endswith("-01-01")
    assert month_calls[1]["start_date"].startswith("202")  # ano anterior


def test_overview_picks_filial_02_series() -> None:
    gateway = FakeGateway()
    service = OverviewService(gateway, branch_access=BranchAccessService())
    payload = service.build(_user(*FULL_PERMS), branch="02")
    assert payload["otd"]["series"][0]["value"] == 88.0


def test_overview_delayed_ops_only_codes_starting_8_or_9() -> None:
    gateway = FakeGateway(
        items=[
            {
                "production_order": "24719201002",
                "op_key": "01|24719201002",
                "product_code": "90350341",
                "product_description": "RESINAGEM CABO",
                "days_late": 5,
                "pending_qty": 0.1,
            },
            {
                "production_order": "CUT",
                "op_key": "01|CUT",
                "product_code": "50120001",
                "product_description": "CORTE DO TUBO ISOLANTE",
                "days_late": 9,
                "pending_qty": 12,
            },
            {
                "production_order": "8OP",
                "op_key": "01|8OP",
                "product_code": "80012849",
                "product_description": "PA 8",
                "days_late": 1,
                "pending_qty": 2,
            },
        ]
    )
    service = OverviewService(gateway, branch_access=BranchAccessService())
    payload = service.build(_user(*FULL_PERMS), branch="01")
    codes = [row["product_code"] for row in payload["delayed_ops"]["items"]]
    assert codes == ["90350341", "80012849"]
    assert payload["delayed_ops"]["count"] == 2
