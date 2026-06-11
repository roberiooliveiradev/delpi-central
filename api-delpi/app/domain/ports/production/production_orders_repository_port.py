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
