"""Port — saldos de estoque por armazém."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Sequence


class StockBalancesQueryRepositoryPort(ABC):
    @abstractmethod
    def fetch_summary(
        self,
        *,
        branches: Sequence[str],
        warehouse: str | None,
        only_positive: bool,
    ) -> dict[str, Any]:
        ...

    @abstractmethod
    def count_items(
        self,
        *,
        branches: Sequence[str],
        warehouse: str | None,
        only_positive: bool,
        product_codes: Sequence[str] | None = None,
    ) -> int:
        ...

    @abstractmethod
    def fetch_items(
        self,
        *,
        branches: Sequence[str],
        warehouse: str | None,
        only_positive: bool,
        sort: str,
        offset: int,
        page_size: int,
        product_codes: Sequence[str] | None = None,
    ) -> list[dict[str, Any]]:
        ...
