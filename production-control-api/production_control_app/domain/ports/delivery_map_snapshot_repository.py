"""Port — snapshot congelado do mapa de entrega (uma fila viva por filial)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Any


class DeliveryMapSnapshotRepositoryPort(ABC):
    @abstractmethod
    def get(self, *, branch: str) -> dict[str, Any] | None:
        """Retorna o snapshot da filial ou None."""

    @abstractmethod
    def upsert(
        self,
        *,
        branch: str,
        horizon_end: date,
        payload: dict[str, Any],
        refreshed_by: str | None,
        schema_version: int = 1,
        source: str = "api-delpi",
    ) -> dict[str, Any]:
        """Substitui o snapshot da filial."""

    @abstractmethod
    def update_payload(self, *, branch: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Atualiza só o JSON (overrides) sem alterar refreshed_at."""
