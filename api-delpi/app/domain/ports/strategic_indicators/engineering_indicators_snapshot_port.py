from __future__ import annotations

from abc import ABC, abstractmethod


class StrategicIndicatorsEngineeringIndicatorsSnapshotPort(ABC):
    @abstractmethod
    def get_engineering_indicators_snapshot(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict]:
        """
        Retorna os indicadores da Engenharia já normalizados para a fase 5.
        """
        raise NotImplementedError