from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_models import (
        StrategicIndicatorsPeriodSnapshot,
    )


class StrategicIndicatorsPeriodScoresRepositoryPort(ABC):
    @abstractmethod
    def list_period_snapshots(
        self,
        *,
        competences: list[str],
        scope_branch: str,
        scope_department_id: str,
    ) -> dict[str, StrategicIndicatorsPeriodSnapshot]:
        raise NotImplementedError

    @abstractmethod
    def upsert_period_snapshot(
        self,
        *,
        snapshot: StrategicIndicatorsPeriodSnapshot,
        scope_branch: str,
        scope_department_id: str,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete_all(self) -> None:
        raise NotImplementedError
