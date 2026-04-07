from __future__ import annotations

from abc import ABC, abstractmethod


class StrategicIndicatorsCommercialIndicatorsSnapshotPort(ABC):
    @abstractmethod
    def get_commercial_indicators_snapshot(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict]:
        """
        Retorna os indicadores do Comercial já normalizados para a fase 5.
        """
        raise NotImplementedError