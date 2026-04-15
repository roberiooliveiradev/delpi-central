from __future__ import annotations

from abc import ABC, abstractmethod


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