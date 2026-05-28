from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_models import (
        PeriodScoresCacheEntry,
        StrategicIndicatorsPeriodSnapshot,
    )


class StrategicIndicatorsPeriodScoresRepositoryPort(ABC):
    @abstractmethod
    def get_period_snapshot(
        self,
        *,
        competence: str,
        scope_branch: str,
        scope_department_id: str,
    ) -> PeriodScoresCacheEntry | None:
        raise NotImplementedError

    @abstractmethod
    def list_period_snapshots(
        self,
        *,
        competences: list[str],
        scope_branch: str,
        scope_department_id: str,
    ) -> dict[str, PeriodScoresCacheEntry]:
        raise NotImplementedError

    @abstractmethod
    def list_period_snapshot_versions(
        self,
        *,
        competence: str,
        scope_branch: str,
        scope_department_id: str,
    ) -> list[PeriodScoresCacheEntry]:
        raise NotImplementedError

    @abstractmethod
    def upsert_period_snapshot(
        self,
        *,
        snapshot: StrategicIndicatorsPeriodSnapshot,
        scope_branch: str,
        scope_department_id: str,
        catalog_inputs_hash: str | None = None,
        is_clean: bool = True,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete_all(self) -> None:
        raise NotImplementedError
