from __future__ import annotations

from abc import ABC, abstractmethod

from app.application.dto.strategic_indicators.catalog_models import (
    StrategicDepartmentCalculatedValue,
)


class StrategicIndicatorsAlertsSummaryPort(ABC):
    @abstractmethod
    def get_alerts_summary(
        self,
        *,
        departments: list[StrategicDepartmentCalculatedValue],
        measurement_errors: list[dict],
    ) -> list[dict]:
        """
        Retorna os alertas resumidos da visão executiva com base
        nos departamentos calculados e nos erros de coleta do período.
        """
        raise NotImplementedError