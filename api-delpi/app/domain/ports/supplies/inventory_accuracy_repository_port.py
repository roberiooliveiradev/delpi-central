"""Port — acuracidade do inventário (SB7 eventos × SD3 INVENT)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Sequence


class InventoryAccuracyRepositoryPort(ABC):
    @abstractmethod
    def fetch_last_closing_date(
        self, *, branches: Sequence[str]
    ) -> str | None:
        """Último fechamento SB9 do escopo (YYYYMMDD) — mês fechado padrão."""
        ...

    @abstractmethod
    def fetch_summary(
        self,
        *,
        branches: Sequence[str],
        period_start: str,
        period_end_exclusive: str,
    ) -> dict[str, Any]:
        """Totais agregados: {"totals": dict, "by_branch": []}."""
        ...

    @abstractmethod
    def count_cancelled_events(
        self,
        *,
        branches: Sequence[str],
        period_start: str,
        period_end_exclusive: str,
    ) -> int:
        """Eventos cancelados (linhas SB7 logicamente deletadas) no período."""
        ...

    @abstractmethod
    def count_items(
        self,
        *,
        branches: Sequence[str],
        period_start: str,
        period_end_exclusive: str,
        outcome: str | None = None,
        search: str | None = None,
    ) -> int:
        ...

    @abstractmethod
    def fetch_items(
        self,
        *,
        branches: Sequence[str],
        period_start: str,
        period_end_exclusive: str,
        outcome: str | None = None,
        search: str | None = None,
        sort: str,
        offset: int,
        page_size: int,
    ) -> list[dict[str, Any]]:
        ...
