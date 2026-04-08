from __future__ import annotations

from abc import ABC, abstractmethod


class StrategicIndicatorsCommercialIndicatorsSnapshotPort(ABC):
    @abstractmethod
    def get_commercial_indicators_snapshot(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict:
        """
        Retorna measurements do Comercial no formato:
        {
            "items": [...],
            "errors": [...]
        }
        """
        raise NotImplementedError