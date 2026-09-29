"""Port — catálogo governado de motivos de parada MES."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class DowntimeReasonRepositoryPort(ABC):
    @abstractmethod
    def get(self, code: str) -> dict[str, Any] | None:
        """Motivo por código estável (minúsculo, aparado)."""

    @abstractmethod
    def list_active(self) -> list[dict[str, Any]]:
        """Motivos ativos, ordenados por sort_order."""

    @abstractmethod
    def set_active(self, code: str, *, active: bool) -> dict[str, Any] | None:
        """Desativa/reativa motivo sem apagar histórico que o referencia."""
