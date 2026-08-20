"""Port — snapshot congelado da carga máquina."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Any


class MachineLoadSnapshotRepositoryPort(ABC):
    @abstractmethod
    def get(
        self,
        *,
        branch: str,
        start_date: date,
        end_date: date,
    ) -> dict[str, Any] | None:
        """Retorna linha com payload_json + refreshed_at, ou None."""

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
        """Insere ou substitui o snapshot do escopo; devolve a linha gravada."""

    @abstractmethod
    def update_payload(
        self,
        *,
        branch: str,
        start_date: date,
        end_date: date,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Atualiza só o JSON (ex.: sequência manual) sem mexer em refreshed_at."""
