"""Port — paradas MES (downtime) do centro de trabalho."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class DowntimeEventRepositoryPort(ABC):
    @abstractmethod
    def get_open(
        self, *, branch: str, work_center: str, conn: Any | None = None
    ) -> dict[str, Any] | None:
        """Parada aberta (ended_at NULL) do CT — no máximo uma por invariante."""

    @abstractmethod
    def get(self, downtime_id: str) -> dict[str, Any] | None:
        """Parada por id."""

    @abstractmethod
    def create(
        self,
        *,
        branch: str,
        work_center: str,
        source: str,
        run_id: str | None = None,
        state_event_id: str | None = None,
        production_order: str | None = None,
        operation_code: str | None = None,
        started_at: datetime | None = None,
    ) -> dict[str, Any]:
        """Abre parada sem motivo; ``DowntimeConflict`` se já houver aberta."""

    @abstractmethod
    def classify(
        self,
        downtime_id: str,
        *,
        reason_code: str,
        planned: bool | None,
        counts_as_availability_loss: bool | None,
        note: str | None = None,
        confirmed_by_type: str | None = None,
        confirmed_by_ref: str | None = None,
        confirmed: bool = True,
    ) -> dict[str, Any]:
        """Aplica motivo + snapshot da classificação; ``DowntimeNotFound``."""

    @abstractmethod
    def close_open(
        self,
        *,
        branch: str,
        work_center: str,
        ended_at: datetime | None = None,
    ) -> dict[str, Any] | None:
        """Encerra a parada aberta do CT; ``None`` se não houver aberta."""

    @abstractmethod
    def list_for_run(self, run_id: str) -> list[dict[str, Any]]:
        """Paradas vinculadas ao run, cronológicas."""

    @abstractmethod
    def list_pending_classification(
        self, run_id: str, *, limit: int = 5
    ) -> list[dict[str, Any]]:
        """Paradas do run sem motivo confirmado (abertas ou já encerradas),
        mais antiga primeiro — alimenta `pendingDowntime` do snapshot."""

    @abstractmethod
    def list_unclassified_for_work_center(
        self,
        *,
        branch: str,
        work_center: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Paradas encerradas do CT ainda sem motivo confirmado, mais
        recente primeiro — alimenta a lista de pendências do cockpit."""

    @abstractmethod
    def list_for_work_center(
        self,
        *,
        branch: str,
        work_center: str,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """Paradas do CT no período, mais recente primeiro."""
