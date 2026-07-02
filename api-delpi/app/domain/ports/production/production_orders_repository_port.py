from typing import Protocol


class ProductionOrdersRepositoryPort(Protocol):
    def fetch_open_orders(
        self,
        *,
        reference_date: str,
        branch: str | None,
        work_center: str | None,
        limit: int,
    ) -> list[dict]: ...

    def fetch_finished_orders(
        self,
        *,
        reference_date: str,
        branch: str | None,
        work_center: str | None,
        limit: int,
    ) -> list[dict]: ...

    def fetch_allocation_gaps(
        self,
        *,
        reference_date: str,
        branch: str | None,
        work_center: str | None,
        limit: int,
    ) -> list[dict]: ...

    def fetch_finished_without_consumption(
        self,
        *,
        reference_date: str,
        branch: str | None,
        work_center: str | None,
        limit: int,
    ) -> list[dict]: ...

    def fetch_planned_vs_real_time(
        self,
        *,
        reference_date: str,
        branch: str | None,
        work_center: str | None,
        limit: int,
    ) -> list[dict]: ...

    def fetch_order_by_production_order(
        self,
        *,
        production_order: str,
        branch: str | None,
        product_type: str | None = None,
    ) -> dict | None: ...

    def search_orders_by_op_prefix(
        self,
        *,
        term: str,
        branches: list[str] | None = None,
        limit: int = 8,
    ) -> list[dict]: ...

    def fetch_linked_pi_orders_by_production_order(
        self,
        *,
        production_order: str,
        branch: str | None,
        sort_by: str | None = None,
        sort_dir: str = "asc",
    ) -> list[dict]: ...
