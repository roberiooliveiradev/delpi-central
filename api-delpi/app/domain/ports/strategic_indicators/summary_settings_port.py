from __future__ import annotations

from abc import ABC, abstractmethod


class StrategicIndicatorsSummarySettingsPort(ABC):
    @abstractmethod
    def get_summary_settings(self) -> dict:
        """
        Retorna os blocos persistidos relevantes para o executive-summary:
        - weights.departments
        - goals.summary
        - parameters.global
        - governance.notes
        - indicators.catalog
        """
        raise NotImplementedError