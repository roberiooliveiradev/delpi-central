from __future__ import annotations

from abc import ABC, abstractmethod


class StrategicIndicatorsAlertsSummaryPort(ABC):
    @abstractmethod
    def get_alerts_summary(self) -> list[dict]:
        """
        Retorna os alertas resumidos da visão executiva.
        """
        raise NotImplementedError