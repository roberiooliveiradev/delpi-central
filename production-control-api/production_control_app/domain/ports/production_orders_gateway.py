from __future__ import annotations

from typing import Any, Protocol, Sequence


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

    def fetch_pcp_orders_catalog(
        self,
        *,
        branch: str,
        page: int,
        page_size: int,
        sort: str,
        open_only: bool | None,
        mother_only: bool | None,
        unbounded_delivery: bool,
        op_key: str | None = None,
        product_code: str | None = None,
        delivery_start: str | None = None,
        delivery_end: str | None = None,
        actual_end_start: str | None = None,
        actual_end_end: str | None = None,
    ) -> dict[str, Any]:
        ...

    def fetch_pcp_orders_catalog_summary(
        self,
        *,
        branch: str,
        open_only: bool | None,
        mother_only: bool | None,
        unbounded_delivery: bool,
        op_key: str | None = None,
        product_code: str | None = None,
        delivery_start: str | None = None,
        delivery_end: str | None = None,
        actual_end_start: str | None = None,
        actual_end_end: str | None = None,
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
        open_only: bool | None = True,
        include_closed: bool = False,
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

    def fetch_operation_materials_batch(
        self,
        *,
        branch: str,
        production_orders: Sequence[str],
    ) -> dict[str, Any]:
        ...

    def fetch_product_physical_locations(
        self,
        *,
        branch: str,
        product_codes: Sequence[str],
    ) -> dict[str, Any]:
        ...

    def fetch_product_inventory_blocks(
        self,
        *,
        branch: str,
        product_codes: Sequence[str],
        warehouse: str = "01",
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

    def fetch_production_order_sets_quantity_mismatches(
        self,
        *,
        branch: str,
        issued_from: str | None,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        ...

    def fetch_production_shared_structure_intermediates(
        self,
        *,
        branch: str,
        movement_from: str,
        lookback_days: int,
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
        product_codes: Sequence[str] | None = None,
    ) -> dict[str, Any]:
        ...

    def fetch_product_internal_movements(
        self,
        *,
        product_code: str,
        branch: str,
        kind: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        page: int = 1,
        page_size: int = 20,
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
