from __future__ import annotations

from app.application.dto.strategic_indicators.get_indicators_response import (
    GetStrategicIndicatorsResponse,
    IndicatorItemResponse,
)
from app.domain.ports.strategic_indicators.engineering_indicators_snapshot_port import (
    StrategicIndicatorsEngineeringIndicatorsSnapshotPort,
)


class GetStrategicIndicatorsUseCase:
    def __init__(
        self,
        engineering_snapshot_port: StrategicIndicatorsEngineeringIndicatorsSnapshotPort,
    ) -> None:
        self._engineering_snapshot_port = engineering_snapshot_port

    def execute(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        department_id: str | None = None,
    ) -> GetStrategicIndicatorsResponse:
        items: list[dict] = []

        if department_id in (None, "", "engineering"):
            engineering_items = self._engineering_snapshot_port.get_engineering_indicators_snapshot(
                start_date=start_date,
                end_date=end_date,
            )
            items.extend(engineering_items)

        return GetStrategicIndicatorsResponse(
            items=[
                IndicatorItemResponse(
                    department_id=item["department_id"],
                    department_name=item["department_name"],
                    indicator_id=item["indicator_id"],
                    indicator_name=item["indicator_name"],
                    weight_pct=int(item["weight_pct"]),
                    goal_2026=item["goal_2026"],
                    scope_type=item["scope_type"],
                    value=float(item["value"]),
                    score=float(item["score"]),
                    gap=float(item["gap"]),
                    trend=item["trend"],
                    classification=item["classification"],
                    source=item["source"],
                )
                for item in items
            ]
        )