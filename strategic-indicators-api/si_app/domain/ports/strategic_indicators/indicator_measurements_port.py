from __future__ import annotations

from abc import ABC, abstractmethod

from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicIndicatorMeasuredValue,
)
from si_app.application.use_cases.strategic_indicators.period_resolution import (
    ResolvedPeriod,
)


class StrategicIndicatorsIndicatorMeasurementsPort(ABC):
    @abstractmethod
    def get_indicator_measurements(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        department_id: str | None = None,
        branch: str | None = None,
    ) -> tuple[list[StrategicIndicatorMeasuredValue], list[dict]]:
        """
        Retorna apenas valores realizados vindos das fontes reais.
        Não deve carregar nome, peso, meta nem descrição oficial.
        """
        raise NotImplementedError

    def get_indicator_measurements_series(
        self,
        *,
        periods: list[ResolvedPeriod],
        department_id: str | None = None,
        branch: str | None = None,
    ) -> dict[str, tuple[list[StrategicIndicatorMeasuredValue], list[dict]]]:
        """
        Retorna medições indexadas por competência.
        Implementação padrão: fallback para chamadas individuais por período.
        """
        result: dict[str, tuple[list[StrategicIndicatorMeasuredValue], list[dict]]] = {}

        for period in periods:
            result[period.competence] = self.get_indicator_measurements(
                start_date=period.start_date,
                end_date=period.end_date,
                department_id=department_id,
                branch=branch,
            )

        return result