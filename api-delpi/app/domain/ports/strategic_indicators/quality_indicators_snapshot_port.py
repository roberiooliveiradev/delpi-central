from __future__ import annotations

from abc import ABC, abstractmethod


class StrategicIndicatorsQualityIndicatorsSnapshotPort(ABC):
    @abstractmethod
    def get_quality_indicators_snapshot(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict]:
        """
        Retorna os indicadores da Qualidade já normalizados para a fase 5.
        """
        raise NotImplementedError