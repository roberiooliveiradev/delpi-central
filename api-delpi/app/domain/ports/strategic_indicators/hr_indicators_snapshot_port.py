from __future__ import annotations

from abc import ABC, abstractmethod


class StrategicIndicatorsHrIndicatorsSnapshotPort(ABC):
    @abstractmethod
    def get_hr_indicators_snapshot(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict:
        """
        Retorna measurements do RH no formato:
        {
            "items": [...],
            "errors": [...]
        }
        """
        raise NotImplementedError