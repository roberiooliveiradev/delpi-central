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


    def fetch_pcp_orders_catalog(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append({"catalog": kwargs})
        items = getattr(self, "order_items", None) or [
            {
                "production_order": "24437001001",
                "op_key": "24437001001",
                "product_code": "90262031",
                "product_description": "WEG MOT",
                "issue_date": "2026-04-02",
                "planned_start_date": "2026-10-28",
                "due_date": "2026-10-28",
                "finish_date": None,
                "planned_qty": 0.1,
                "pending_qty": 0.1,
                "observation": "WEG_MOT",
                "is_open": True,
                "is_mother": True,
                "branch": kwargs.get("branch") or "01",
            }
        ]
        return {
            "success": True,
            "data": {
                "items": items,
                "pagination": {
                    "page": kwargs.get("page") or 1,
                    "page_size": kwargs.get("page_size") or 50,
                    "total": len(items),
                },
            },
        }

    def fetch_pcp_orders_catalog_summary(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append({"catalog_summary": kwargs})
        items = getattr(self, "order_items", None)
        count = len(items) if items is not None else 1
        return {
            "success": True,
            "data": {
                "summary": {
                    "total_orders": count,
                    "open_orders": count,
                    "planned_qty_sum": 0.1,
                    "pending_qty_sum": 0.1,
                }
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
    assert payload["filters"]["excluded_product_code_prefixes"] == ["9035"]
    assert payload["summary"]["product_count"] == 1
    assert payload["summary"]["total_quantity"] == 10.0
    assert payload["summary"]["total_stock_value"] == 25.0
    assert gateway.calls[0]["warehouse"] == "01"
    assert gateway.calls[0]["branch"] == "01"


def test_stock_balances_excludes_9035_prefix() -> None:
    gateway = FakeGateway(
        pages=[
            [
                {
                    "product_code": "90350341",
                    "description": "Família excluída",
                    "branch": "01",
                    "warehouse": "01",
                    "quantity": 7,
                    "unit_cost": 1,
                    "stock_value": 7,
                },
                {
                    "product_code": "90260014",
                    "description": "PA ok",
                    "branch": "01",
                    "warehouse": "01",
                    "quantity": 2,
                    "unit_cost": 3,
                    "stock_value": 6,
                },
            ]
        ]
    )
    service = _service(gateway)
    payload = service.stock_balances(_user(*FULL_PERMS), branch="01")
    codes = [row["product_code"] for row in payload["items"]]
    assert codes == ["90260014"]
    assert payload["summary"]["product_count"] == 1


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


def test_reports_catalog_lists_stock_balances_and_production_orders() -> None:
    gateway = FakeGateway()
    service = _service(gateway)
    catalog = service.list_catalog(_user(*FULL_PERMS), branch="01")
    ids = [item["id"] for item in catalog["reports"]]
    assert ids == ["stock-balances", "production-orders"]
    assert catalog["reports"][0]["icon"] == "warehouse"
    assert catalog["reports"][0]["eyebrow"] == "Estoque"
    assert catalog["reports"][1]["icon"] == "clipboard-list"
    assert catalog["reports"][1]["eyebrow"] == "Produção"


def test_email_schedule_defaults_when_missing() -> None:
    class Gateway(FakeGateway):
        def get_personal_stock_balances_subscription(self, **kwargs):
            return {"success": True, "data": None}

    user = _user(*FULL_PERMS)
    user.id = "user-1"
    user.email = "user@delpi.com.br"
    service = _service(Gateway())
    payload = service.get_email_schedule(user, branch="01")
    assert payload["configured"] is False
    assert payload["hour"] == 7
    assert payload["scheduleKind"] == "weekdays"


def test_upsert_email_schedule_maps_response() -> None:
    class Gateway(FakeGateway):
        def upsert_personal_stock_balances_subscription(self, **kwargs):
            assert kwargs["branch"] == "02"
            assert kwargs["hour"] == 8
            return {
                "success": True,
                "data": {
                    "configured": True,
                    "definition": {"id": "def-1"},
                    "schedule": {
                        "scheduleKind": "weekdays",
                        "enabled": True,
                        "hour": 8,
                        "minute": 15,
                        "timezone": "America/Sao_Paulo",
                        "nextRunAt": "2026-08-29T11:15:00+00:00",
                        "cronExpression": "15 8 * * 1-5",
                    },
                },
            }

    user = _user(*FULL_PERMS)
    user.id = "user-1"
    user.email = "user@delpi.com.br"
    service = _service(Gateway())
    payload = service.upsert_email_schedule(user, branch="02", hour=8, minute=15, enabled=True)
    assert payload["configured"] is True
    assert payload["hour"] == 8
    assert payload["minute"] == 15
    assert payload["definitionId"] == "def-1"


def test_production_orders_defaults_to_open_unbounded() -> None:
    gateway = FakeGateway()
    service = _service(gateway)
    payload = service.production_orders(_user(*FULL_PERMS), branch="01")

    catalog_calls = [call["catalog"] for call in gateway.calls if "catalog" in call]
    assert catalog_calls[0]["open_only"] is True
    assert catalog_calls[0]["unbounded_delivery"] is True
    assert catalog_calls[0]["mother_only"] is None
    assert catalog_calls[0]["sort"] == "op_asc"
    assert payload["report_id"] == "production-orders"
    assert payload["items"][0]["production_order"] == "24437001001"
    assert payload["items"][0]["product_code"] == "90262031"
    assert payload["items"][0]["planned_qty"] == 0.1
    assert payload["items"][0]["pending_qty"] == 0.1
    assert payload["items"][0]["observation"] == "WEG_MOT"
    assert payload["summary"]["order_count"] == 1
    assert payload["filters"]["open_only"] is True
    assert payload["filters"]["unbounded_delivery"] is True


def test_production_orders_passes_mother_and_product_filters() -> None:
    gateway = FakeGateway()
    service = _service(gateway)
    payload = service.production_orders(
        _user(*FULL_PERMS),
        branch="02",
        op_key="244370",
        product_code="90262031",
        mother_only=True,
        open_only=True,
        sort="delivery_asc",
    )
    catalog_calls = [call["catalog"] for call in gateway.calls if "catalog" in call]
    assert catalog_calls[0]["branch"] == "02"
    assert catalog_calls[0]["op_key"] == "244370"
    assert catalog_calls[0]["product_code"] == "90262031"
    assert catalog_calls[0]["mother_only"] is True
    assert catalog_calls[0]["sort"] == "delivery_asc"
    assert payload["filters"]["mother_only"] is True


def test_production_orders_uses_delivery_window_when_dates_are_set() -> None:
    gateway = FakeGateway()
    service = _service(gateway)
    payload = service.production_orders(
        _user(*FULL_PERMS),
        branch="01",
        delivery_start="2026-01-01",
        delivery_end="2026-12-31",
        open_only=False,
    )
    catalog_calls = [call["catalog"] for call in gateway.calls if "catalog" in call]
    assert catalog_calls[0]["unbounded_delivery"] is False
    assert catalog_calls[0]["delivery_start"] == "2026-01-01"
    assert catalog_calls[0]["delivery_end"] == "2026-12-31"
    assert catalog_calls[0]["open_only"] is False
    assert payload["filters"]["unbounded_delivery"] is False


def test_production_orders_all_skips_open_flag() -> None:
    gateway = FakeGateway()
    service = _service(gateway)
    payload = service.production_orders(_user(*FULL_PERMS), branch="01", open_only="all")
    catalog_calls = [call["catalog"] for call in gateway.calls if "catalog" in call]
    assert catalog_calls[0]["open_only"] is None
    assert payload["filters"]["open_only"] is None


def test_production_orders_passes_actual_end_only_when_closed() -> None:
    gateway = FakeGateway()
    service = _service(gateway)
    payload = service.production_orders(
        _user(*FULL_PERMS),
        branch="01",
        open_only=False,
        actual_end_start="2026-01-01",
        actual_end_end="2026-06-30",
    )
    catalog_calls = [call["catalog"] for call in gateway.calls if "catalog" in call]
    assert catalog_calls[0]["open_only"] is False
    assert catalog_calls[0]["actual_end_start"] == "2026-01-01"
    assert catalog_calls[0]["actual_end_end"] == "2026-06-30"
    assert payload["filters"]["actual_end_start"] == "2026-01-01"
    assert payload["filters"]["actual_end_end"] == "2026-06-30"


def test_production_orders_drops_actual_end_when_open() -> None:
    gateway = FakeGateway()
    service = _service(gateway)
    payload = service.production_orders(
        _user(*FULL_PERMS),
        branch="01",
        open_only=True,
        actual_end_start="2026-01-01",
        actual_end_end="2026-06-30",
    )
    catalog_calls = [call["catalog"] for call in gateway.calls if "catalog" in call]
    assert catalog_calls[0]["open_only"] is True
    assert catalog_calls[0]["actual_end_start"] is None
    assert catalog_calls[0]["actual_end_end"] is None
    assert payload["filters"]["actual_end_start"] is None
    assert payload["filters"]["actual_end_end"] is None


def test_production_orders_drops_actual_end_when_all() -> None:
    gateway = FakeGateway()
    service = _service(gateway)
    payload = service.production_orders(
        _user(*FULL_PERMS),
        branch="01",
        open_only="all",
        actual_end_start="2026-01-01",
        actual_end_end="2026-06-30",
    )
    catalog_calls = [call["catalog"] for call in gateway.calls if "catalog" in call]
    assert catalog_calls[0]["open_only"] is None
    assert catalog_calls[0]["actual_end_start"] is None
    assert catalog_calls[0]["actual_end_end"] is None
    assert payload["filters"]["actual_end_start"] is None


def test_production_orders_rejects_unknown_sort() -> None:
    gateway = FakeGateway()
    service = _service(gateway)
    payload = service.production_orders(
        _user(*FULL_PERMS),
        branch="01",
        sort="not-a-sort",
    )
    catalog_calls = [call["catalog"] for call in gateway.calls if "catalog" in call]
    assert catalog_calls[0]["sort"] == "op_asc"
    assert payload["filters"]["sort"] == "op_asc"
