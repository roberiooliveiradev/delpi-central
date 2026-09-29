"""Port — timeline MES do estado operacional do centro de trabalho."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class WorkCenterStateRepositoryPort(ABC):
    @abstractmethod
    def get_open(
        self, *, branch: str, work_center: str
    ) -> dict[str, Any] | None:
        """Estado aberto (ended_at NULL) do CT — no máximo um por invariante."""

    @abstractmethod
    def open_event(
        self,
        *,
        branch: str,
        work_center: str,
        state: str,
        source: str,
        run_id: str | None = None,
        started_at: datetime | None = None,
    ) -> dict[str, Any]:
        """Abre um evento de estado; ``MesStateConflict`` se já houver aberto."""

    @abstractmethod
    def close_open(
        self,
        *,
        branch: str,
        work_center: str,
        ended_at: datetime | None = None,
    ) -> dict[str, Any] | None:
        """Encerra o estado aberto do CT; ``None`` se não houver aberto."""

    @abstractmethod
    def list_for_work_center(
        self,
        *,
        branch: str,
        work_center: str,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """Timeline do CT, mais recente primeiro."""

    @abstractmethod
    def list_for_run(self, run_id: str) -> list[dict[str, Any]]:
        """Timeline de estados vinculados a um run, cronológica."""
