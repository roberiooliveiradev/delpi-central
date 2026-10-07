"""Porta do repositório de ajustes de inventário (SD3 doc='INVENT')."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class InventoryAdjustmentsRepositoryPort(ABC):
    @abstractmethod
    def fetch_adjustment_items(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: Optional[str],
        product_code: Optional[str],
        warehouse: Optional[str],
        nature: Optional[str],
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        """Página de ajustes com total (items + total)."""

    @abstractmethod
    def fetch_adjustment_summary(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: Optional[str],
        product_code: Optional[str],
        warehouse: Optional[str],
        nature: Optional[str],
    ) -> dict[str, Any]:
        """Agregados do período: totals + by_month + by_branch + by_nature."""
