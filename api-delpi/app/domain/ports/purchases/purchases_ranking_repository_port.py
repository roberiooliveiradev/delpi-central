from typing import Protocol


class PurchasesRankingRepositoryPort(Protocol):
    def fetch_top_products(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str | None,
        limit: int,
    ) -> list[dict]: ...
