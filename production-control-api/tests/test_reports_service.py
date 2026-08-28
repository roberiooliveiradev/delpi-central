from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from production_control_app.application.services.reports_service import (
    ReportsService,
    _StockBalancesSnapshotCache,
)
from production_control_app.domain.services.branch_access_service import BranchAccessService


class FakeGateway:
    def __init__(self, pages: list[list[dict[str, Any]]] | None = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self.pages = pages or [
            [
                {
                    "product_code": "9001234",
                    "description": "Transformador A",
                    "branch": "01",
                    "warehouse": "01",
                    "quantity": 10,
                    "unit_cost": 2.5,
                    "stock_value": 25,
                },
                {
                    "product_code": "50120001",
                    "description": "MP ignorada",
                    "branch": "01",
                    "warehouse": "01",
                    "quantity": 99,
                    "unit_cost": 1,
                    "stock_value": 99,
                },
                {
                    "product_code": "80012849",
                    "description": "Amostra",
                    "branch": "01",
                    "warehouse": "01",
                    "quantity": 3,
                    "unit_cost": 4,
                    "stock_value": 12,
                },
            ]
        ]

    def fetch_stock_balances_items(
        self,
        *,
        branch: str,
        warehouse: str,
        only_positive: bool = True,
        page: int = 1,
        page_size: int = 500,
        sort: str = "product_code_asc",
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "branch": branch,
                "warehouse": warehouse,
                "only_positive": only_positive,
                "page": page,
                "page_size": page_size,
                "sort": sort,
            }
        )
        index = page - 1
        items = self.pages[index] if 0 <= index < len(self.pages) else []
        total = sum(len(chunk) for chunk in self.pages)
        return {
            "success": True,
            "data": {
                "items": items,
                "pagination": {"page": page, "page_size": page_size, "total": total},
            },
        }


def _user(*permissions: str):
    return SimpleNamespace(is_superadmin=False, permissions=list(permissions))


FULL_PERMS = (
    "production-control.access",
    "production-control.reports.view",
    "production-control.view.filial-01",
    "production-control.view.filial-02",
)


def _service(gateway: FakeGateway) -> ReportsService:
    return ReportsService(
        gateway,
        branch_access=BranchAccessService(),
        cache=_StockBalancesSnapshotCache(300),
    )


def test_stock_balances_branch_01_keeps_only_prefix_9() -> None:
    gateway = FakeGateway()
    service = _service(gateway)
    payload = service.stock_balances(_user(*FULL_PERMS), branch="01")

    codes = [row["product_code"] for row in payload["items"]]
    assert codes == ["9001234"]
    assert payload["filters"]["warehouse"] == "01"
    assert payload["filters"]["product_code_prefixes"] == ["9"]
    assert payload["summary"]["product_count"] == 1
    assert payload["summary"]["total_quantity"] == 10.0
    assert payload["summary"]["total_stock_value"] == 25.0
    assert gateway.calls[0]["warehouse"] == "01"
    assert gateway.calls[0]["branch"] == "01"


def test_stock_balances_branch_02_keeps_prefixes_8_and_9() -> None:
    gateway = FakeGateway()
    service = _service(gateway)
    payload = service.stock_balances(_user(*FULL_PERMS), branch="02")

    codes = [row["product_code"] for row in payload["items"]]
    assert codes == ["80012849", "9001234"]
    assert payload["filters"]["product_code_prefixes"] == ["8", "9"]
    assert payload["summary"]["product_count"] == 2
    assert payload["summary"]["total_quantity"] == 13.0
    assert payload["summary"]["total_stock_value"] == 37.0


def test_stock_balances_search_filters_description() -> None:
    gateway = FakeGateway()
    service = _service(gateway)
    empty = service.stock_balances(_user(*FULL_PERMS), branch="01", search="amostra")
    assert empty["items"] == []
    payload = service.stock_balances(_user(*FULL_PERMS), branch="02", search="amostra")
    assert len(payload["items"]) == 1
    assert payload["items"][0]["product_code"] == "80012849"


def test_stock_balances_large_page_size_for_excel_export() -> None:
    gateway = FakeGateway()
    service = _service(gateway)
    payload = service.stock_balances(
        _user(*FULL_PERMS),
        branch="02",
        page=1,
        page_size=5000,
    )
    assert payload["pagination"]["page_size"] == 5000
    assert payload["pagination"]["total"] == 2
    assert len(payload["items"]) == 2


def test_stock_balances_cache_skips_gateway_on_next_page() -> None:
    gateway = FakeGateway()
    service = _service(gateway)
    first = service.stock_balances(_user(*FULL_PERMS), branch="01", page=1, page_size=1)
    calls_after_first = len(gateway.calls)
    assert first["pagination"]["total"] == 1
    second = service.stock_balances(_user(*FULL_PERMS), branch="01", page=1, page_size=1)
    assert len(gateway.calls) == calls_after_first
    assert second["items"] == first["items"]


def test_stock_balances_refresh_bypasses_cache() -> None:
    gateway = FakeGateway()
    service = _service(gateway)
    service.stock_balances(_user(*FULL_PERMS), branch="01")
    calls_after_first = len(gateway.calls)
    service.stock_balances(_user(*FULL_PERMS), branch="01", refresh=True)
    assert len(gateway.calls) > calls_after_first


def test_reports_catalog_lists_stock_balances() -> None:
    gateway = FakeGateway()
    service = _service(gateway)
    catalog = service.list_catalog(_user(*FULL_PERMS), branch="01")
    assert catalog["reports"][0]["id"] == "stock-balances"
    assert catalog["reports"][0]["icon"] == "warehouse"
    assert catalog["reports"][0]["eyebrow"] == "Estoque"
