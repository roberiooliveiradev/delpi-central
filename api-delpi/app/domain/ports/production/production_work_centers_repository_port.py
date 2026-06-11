from typing import Protocol


class ProductionWorkCentersRepositoryPort(Protocol):
    def fetch_order_summary(
        self,
        *,
        reference_date: str,
        branch: str | None,
        limit: int,
    ) -> list[dict]: ...

    def fetch_average_planned_time(
        self,
        *,
        reference_date: str,
        branch: str | None,
        limit: int,
    ) -> list[dict]: ...
