"""Port — saldos de estoque por armazém."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class StockBalancesQueryRepositoryPort(ABC):
    @abstractmethod
    def fetch_summary(
        self,
        *,
        branch: str | None,
        warehouse: str | None,
        only_positive: bool,
    ) -> dict[str, Any]:
        ...

    @abstractmethod
    def count_items(
        self,
        *,
        branch: str | None,
        warehouse: str | None,
        only_positive: bool,
    ) -> int:
        ...

    @abstractmethod
    def fetch_items(
        self,
        *,
        branch: str | None,
        warehouse: str | None,
        only_positive: bool,
        sort: str,
        offset: int,
        page_size: int,
    ) -> list[dict[str, Any]]:
        ...
