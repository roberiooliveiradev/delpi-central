from __future__ import annotations

from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_service import (
    StrategicIndicatorsSnapshotService,
)


class GetDashboardDepartmentScoreUseCase:
    def __init__(
        self,
        *,
        snapshot_service: StrategicIndicatorsSnapshotService,
    ) -> None:
        self._snapshot_service = snapshot_service

    def execute(
        self,
        *,
        department_id: str,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
    ) -> dict | None:
        normalized_id = department_id.strip()
        if not normalized_id:
            return None

        department, measurement_errors = (
            self._snapshot_service.get_dashboard_department_snapshot(
                department_id=normalized_id,
                competence=competence,
                start_date=start_date,
                end_date=end_date,
                branch=branch,
            )
        )
        if department is None:
            return None

        return {
            "department_id": department.department_id,
            "department_name": department.department_name,
            "score": department.score,
            "classification": department.classification,
            "contribution": department.contribution,
            "variation": None,
            "partial_success": len(measurement_errors) > 0,
        }
