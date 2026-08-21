"""Port — conjuntos de ordens de produção (detector de conjunto incompleto)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ProductionOrderSetsRepositoryPort(ABC):
    @abstractmethod
    def get_incomplete_sets_summary(
        self,
        *,
        branch: str | None,
        issued_from: str | None = None,
    ) -> dict[str, Any]:
        ...

    @abstractmethod
    def get_incomplete_sets(
        self,
        *,
        offset: int,
        page_size: int,
        branch: str | None,
        issued_from: str | None = None,
    ) -> list[dict[str, Any]]:
        ...
