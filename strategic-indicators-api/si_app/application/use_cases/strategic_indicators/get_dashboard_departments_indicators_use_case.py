from __future__ import annotations

from si_app.application.use_cases.strategic_indicators.get_dashboard_department_indicators_use_case import (
    GetDashboardDepartmentIndicatorsUseCase,
)
from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_service import (
    StrategicIndicatorsSnapshotService,
)
from si_app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)


class GetDashboardDepartmentsIndicatorsUseCase:
    """Todos os departamentos com IDD + indicadores (metas e realizado)."""

    def __init__(
        self,
        *,
        snapshot_service: StrategicIndicatorsSnapshotService,
        calculator: StrategicIndicatorsCalculator,
    ) -> None:
        self._snapshot_service = snapshot_service
        self._mapper = GetDashboardDepartmentIndicatorsUseCase(
            snapshot_service=snapshot_service,
            calculator=calculator,
        )

    def execute(
        self,
        *,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
        department_id: str | None = None,
    ) -> dict:
        snapshot = self._snapshot_service.get_current_and_previous_snapshot(
            competence=competence,
            start_date=start_date,
            end_date=end_date,
            department_id=None,
            branch=branch,
        )
        catalog_by_id = {
            item.indicator_id: item
            for item in snapshot.catalog.indicators_catalog
        }
        period = snapshot.current.period
        normalized_filter = (department_id or "").strip() or None

        items = []
        for department in snapshot.current.calculated_departments:
            if (
                normalized_filter is not None
                and department.department_id != normalized_filter
            ):
                continue
            items.append(
                {
                    "department_id": department.department_id,
                    "department_name": department.department_name,
                    "short_name": department.short_name,
                    "idd": department.score,
                    "score": department.score,
                    "classification": department.classification,
                    "contribution": department.contribution,
                    "aggregation_mode": department.aggregation_mode,
                    "indicators": [
                        self._mapper.map_indicator(
                            indicator=indicator,
                            catalog_item=catalog_by_id.get(indicator.indicator_id),
                            start_date=period.start_date,
                            end_date=period.end_date,
                            competence=period.competence,
                        )
                        for indicator in department.indicators
                    ],
                }
            )

        return {
            "items": items,
            "partial_success": len(snapshot.current.measurement_errors) > 0,
            "errors": snapshot.current.measurement_errors,
        }
