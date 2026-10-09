"""Port — matérias-primas sem giro (SB2 × SD3/SB9)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Sequence


class NonMovingStockRepositoryPort(ABC):
    @abstractmethod
    def fetch_summary(
        self,
        *,
        branches: Sequence[str],
        warehouses: Sequence[str],
        window_start: str,
        window_end: str,
        no_consumption_status: str,
    ) -> dict[str, Any]:
        """Totais agregados: {"totals": dict, "by_status": [], "by_branch": []}."""
        ...

    @abstractmethod
    def count_items(
        self,
        *,
        branches: Sequence[str],
        warehouses: Sequence[str],
        window_start: str,
        window_end: str,
        no_consumption_status: str,
        product_codes: Sequence[str] | None = None,
        turnover_status: str | None = None,
        blocked: bool | None = None,
        search: str | None = None,
    ) -> int:
        ...

    @abstractmethod
    def fetch_items(
        self,
        *,
        branches: Sequence[str],
        warehouses: Sequence[str],
        window_start: str,
        window_end: str,
        no_consumption_status: str,
        product_codes: Sequence[str] | None = None,
        turnover_status: str | None = None,
        blocked: bool | None = None,
        search: str | None = None,
        sort: str,
        offset: int,
        page_size: int,
    ) -> list[dict[str, Any]]:
        ...
