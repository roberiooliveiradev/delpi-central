from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from si_app.application.dto.strategic_indicators.catalog_models import (
        StrategicIndicatorMeasuredValue,
    )
    from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_models import (
        StrategicIndicatorsCatalogSnapshot,
    )
    from si_app.application.services.strategic_indicators.period_resolution import (
        ResolvedPeriod,
    )


class StrategicIndicatorsCalculationSnapshotsRepositoryPort(ABC):
    @abstractmethod
    def upsert_calculation_snapshot(
        self,
        *,
        period: ResolvedPeriod,
        catalog: StrategicIndicatorsCatalogSnapshot,
        measurements: list[StrategicIndicatorMeasuredValue],
        measurement_errors: list[dict],
        scope_branch: str,
        scope_department_id: str,
        catalog_inputs_hash: str | None = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete_all(self) -> None:
        raise NotImplementedError
