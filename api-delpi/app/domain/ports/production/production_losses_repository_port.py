from typing import Protocol


class ProductionLossesRepositoryPort(Protocol):
    def fetch_loss_records(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str | None,
        limit: int,
        loss_type: str,
    ) -> list[dict]: ...

    def fetch_top_materials(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str | None,
        limit: int,
        loss_type: str,
    ) -> list[dict]: ...
