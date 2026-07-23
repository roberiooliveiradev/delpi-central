from typing import Protocol


class ProductionMachineProgramsRepositoryPort(Protocol):
    def fetch_top_intermediates(
        self,
        *,
        branch: str,
        date_start: str,
        date_end_exclusive: str,
        page: int,
        page_size: int,
        search: str | None = None,
    ) -> tuple[list[dict], int]: ...
