from __future__ import annotations

from abc import ABC, abstractmethod

from si_app.application.services.strategic_indicators.period_resolution import (
    ResolvedPeriod,
)


class StrategicIndicatorsEngineeringIndicatorsSnapshotPort(ABC):
    @abstractmethod
    def get_engineering_indicators_snapshot(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
    ) -> dict:
        """
        Retorna measurements da Engenharia no formato:
        {
            "items": [...],
            "errors": [...]
        }
        """
        raise NotImplementedError

    def get_engineering_indicators_snapshot_series(
        self,
        *,
        periods: list[ResolvedPeriod],
        branch: str | None = None,
    ) -> dict[str, dict]:
        result: dict[str, dict] = {}

        for period in periods:
            result[period.competence] = self.get_engineering_indicators_snapshot(
                start_date=period.start_date,
                end_date=period.end_date,
                branch=branch,
            )

        return result