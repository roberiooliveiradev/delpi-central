from __future__ import annotations

from abc import ABC, abstractmethod


class StrategicIndicatorsExecutiveSummaryRepositoryPort(ABC):
    @abstractmethod
    def get_executive_summary(self) -> dict:
        raise NotImplementedError