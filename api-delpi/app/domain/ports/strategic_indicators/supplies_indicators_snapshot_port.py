from __future__ import annotations

from abc import ABC, abstractmethod

from app.application.use_cases.strategic_indicators.period_resolution import (
    ResolvedPeriod,
)


class StrategicIndicatorsSuppliesIndicatorsSnapshotPort(ABC):
    @abstractmethod
    def get_supplies_indicators_snapshot(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
    ) -> dict:
        raise NotImplementedError

    def get_supplies_indicators_snapshot_series(
        self,
        *,
        periods: list[ResolvedPeriod],
        branch: str | None = None,
    ) -> dict[str, dict]:
        result: dict[str, dict] = {}

        for period in periods:
            result[period.competence] = self.get_supplies_indicators_snapshot(
                start_date=period.start_date,
                end_date=period.end_date,
                branch=branch,
            )

        return result