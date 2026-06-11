from typing import Protocol


class ProductionConsumptionRepositoryPort(Protocol):
    def fetch_top_items(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str | None,
        limit: int,
        group_by: str,
    ) -> list[dict]: ...
