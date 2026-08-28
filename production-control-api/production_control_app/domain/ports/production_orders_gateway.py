from __future__ import annotations

from typing import Any, Protocol


class ProductionOrdersGateway(Protocol):
    def fetch_pcp_orders_summary(self, *, branch: str) -> dict[str, Any]:
        ...

    def fetch_pcp_orders_items(
        self,
        *,
        branch: str,
        delayed_only: bool,
        page_size: int,
    ) -> dict[str, Any]:
        ...

    def fetch_pcp_orders_items_page(
        self,
        *,
        branch: str,
        delivery_start: str,
        delivery_end: str,
        page: int,
        page_size: int,
        sort: str = "delivery_asc",
        mother_only: bool = True,
        open_only: bool = True,
    ) -> dict[str, Any]:
        ...

    def fetch_production_otd(
        self,
        *,
        branch: str,
        start_date: str,
        end_date: str,
        page_size: int,
    ) -> dict[str, Any]:
        ...

    def fetch_production_otd_series(
        self,
        *,
        branch: str,
        start_date: str,
        end_date: str,
        granularity: str,
    ) -> dict[str, Any]:
        ...

    def fetch_machine_load_work_centers(
        self,
        *,
        branch: str,
        delivery_start: str | None,
        delivery_end: str,
    ) -> dict[str, Any]:
        ...

    def fetch_machine_load_operations(
        self,
        *,
        branch: str,
        delivery_start: str | None = None,
        delivery_end: str | None = None,
        scheduled_start: str | None = None,
        scheduled_end: str | None = None,
        production_order: str | None = None,
        work_center: str | None = None,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        ...

    def fetch_machine_load_appointment_status(
        self,
        *,
        branch: str,
        items: list[dict[str, str]],
    ) -> dict[str, Any]:
        ...

    def fetch_production_order_sets_incomplete(
        self,
        *,
        branch: str,
        issued_from: str | None,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        ...

    def fetch_production_appointments_series(
        self,
        *,
        branch: str,
        start_date: str,
        end_date: str,
        granularity: str,
    ) -> dict[str, Any]:
        ...

    def fetch_purchase_request_open_coverage(self, *, branch: str) -> dict[str, Any]:
        ...

    def fetch_finished_product_shortages(
        self, *, product_code: str, branch: str
    ) -> dict[str, Any]:
        ...

    def fetch_open_sales_orders(self) -> dict[str, Any]:
        ...

    def fetch_open_production_orders(self) -> dict[str, Any]:
        ...

    def fetch_recently_closed_orders(self, *, days: int) -> dict[str, Any]:
        ...

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
        ...

    def get_personal_stock_balances_subscription(
        self,
        *,
        user_id: str,
        branch: str,
    ) -> dict[str, Any]:
        ...

    def upsert_personal_stock_balances_subscription(
        self,
        *,
        user_id: str,
        email: str,
        branch: str,
        hour: int,
        minute: int,
        enabled: bool,
        timezone_name: str = "America/Sao_Paulo",
    ) -> dict[str, Any]:
        ...
