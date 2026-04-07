from __future__ import annotations

from abc import ABC, abstractmethod

from app.application.dto.strategic_indicators.catalog_models import (
    StrategicIndicatorMeasuredValue,
)


class StrategicIndicatorsIndicatorMeasurementsPort(ABC):
    @abstractmethod
    def get_indicator_measurements(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        department_id: str | None = None,
    ) -> tuple[list[StrategicIndicatorMeasuredValue], list[dict]]:
        """
        Retorna apenas valores realizados vindos das fontes reais.
        Não deve carregar nome, peso, meta nem descrição oficial.
        """
        raise NotImplementedError