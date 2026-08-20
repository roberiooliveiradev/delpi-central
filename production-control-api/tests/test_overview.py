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

    kinds = {name for name, _ in gateway.calls}
    assert kinds == {"otd", "otd_series", "items"}
    series_call = next(params for name, params in gateway.calls if name == "otd_series")
    assert series_call["granularity"] == "day"
    assert series_call["branch"] == "01"


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
