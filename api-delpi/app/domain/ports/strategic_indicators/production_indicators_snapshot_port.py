from __future__ import annotations

from abc import ABC, abstractmethod


class StrategicIndicatorsProductionIndicatorsSnapshotPort(ABC):
    @abstractmethod
    def get_production_indicators_snapshot(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict:
        """
        Retorna measurements da Produção no formato:
        {
            "items": [...],
            "errors": [...]
        }
        """
        raise NotImplementedError