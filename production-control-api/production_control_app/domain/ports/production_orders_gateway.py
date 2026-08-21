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
        delivery_start: str | None,
        delivery_end: str,
        work_center: str | None,
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

    def fetch_open_sales_orders(self) -> dict[str, Any]:
        ...

    def fetch_open_production_orders(self) -> dict[str, Any]:
        ...

    def fetch_recently_closed_orders(self, *, days: int) -> dict[str, Any]:
        ...
