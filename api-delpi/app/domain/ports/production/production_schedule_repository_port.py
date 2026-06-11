from typing import Protocol


class ProductionScheduleRepositoryPort(Protocol):
    def fetch_schedule_today(
        self,
        *,
        reference_date: str,
        branch: str | None,
        limit: int,
    ) -> list[dict]: ...
