from __future__ import annotations

from abc import ABC, abstractmethod


class StrategicIndicatorsFinancialIndicatorsSnapshotPort(ABC):
    @abstractmethod
    def get_financial_indicators_snapshot(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict:
        raise NotImplementedError