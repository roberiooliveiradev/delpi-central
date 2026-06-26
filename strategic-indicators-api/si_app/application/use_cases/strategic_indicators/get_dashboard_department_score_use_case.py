from __future__ import annotations

from si_app.application.use_cases.strategic_indicators.get_departments_real_use_case import (
    GetStrategicIndicatorsDepartmentsRealRequest,
    GetStrategicIndicatorsDepartmentsRealUseCase,
)


class GetDashboardDepartmentScoreUseCase:
    def __init__(
        self,
        *,
        departments_use_case: GetStrategicIndicatorsDepartmentsRealUseCase,
    ) -> None:
        self._departments_use_case = departments_use_case

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

        result = self._departments_use_case.execute(
            GetStrategicIndicatorsDepartmentsRealRequest(
                department_id=normalized_id,
                branch=branch,
                start_date=start_date,
                end_date=end_date,
                competence=competence,
            )
        )

        items = result.get("items") or []
        match = next(
            (item for item in items if item.get("id") == normalized_id),
            items[0] if items else None,
        )
        if match is None:
            return None

        return {
            "department_id": match["id"],
            "department_name": match.get("name"),
            "score": match.get("score"),
            "classification": match.get("classification"),
            "contribution": match.get("contribution"),
            "variation": match.get("variation"),
            "partial_success": bool(result.get("partial_success")),
        }
