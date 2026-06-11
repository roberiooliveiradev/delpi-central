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

    def fetch_top_items_by_work_center(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str | None,
        work_center: str | None,
        limit: int,
    ) -> list[dict]: ...

    def fetch_top_items_validated(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str | None,
        limit: int,
    ) -> list[dict]: ...

    def fetch_consumption_by_item(
        self,
        *,
        item_code: str,
        date_start: str,
        date_end_inclusive: str,
        branch: str | None,
        product_group: str | None,
        limit: int,
    ) -> list[dict]: ...
