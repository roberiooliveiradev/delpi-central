"""Port — snapshot congelado da carga máquina (uma fila viva por filial)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Any


class MachineLoadSnapshotRepositoryPort(ABC):
    @abstractmethod
    def get(self, *, branch: str) -> dict[str, Any] | None:
        """Retorna a fila da filial (payload_json + janela + refreshed_at), ou None."""

    @abstractmethod
    def upsert(
        self,
        *,
        branch: str,
        start_date: date,
        end_date: date,
        payload: dict[str, Any],
        refreshed_by: str | None,
        schema_version: int = 1,
        source: str = "api-delpi",
    ) -> dict[str, Any]:
        """Substitui a fila da filial; ``start_date``/``end_date`` são a janela puxada."""

    @abstractmethod
    def update_payload(self, *, branch: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Atualiza só o JSON (ex.: sequência manual) sem mexer em refreshed_at."""
