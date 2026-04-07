from __future__ import annotations

from app.application.dto.strategic_indicators.get_indicators_response import (
    GetStrategicIndicatorsResponse,
    IndicatorFetchErrorResponse,
    IndicatorItemResponse,
)
from app.domain.ports.strategic_indicators.commercial_indicators_snapshot_port import (
    StrategicIndicatorsCommercialIndicatorsSnapshotPort,
)
from app.domain.ports.strategic_indicators.engineering_indicators_snapshot_port import (
    StrategicIndicatorsEngineeringIndicatorsSnapshotPort,
)
from app.domain.ports.strategic_indicators.production_indicators_snapshot_port import (
    StrategicIndicatorsProductionIndicatorsSnapshotPort,
)
from app.domain.ports.strategic_indicators.quality_indicators_snapshot_port import (
    StrategicIndicatorsQualityIndicatorsSnapshotPort,
)


class GetStrategicIndicatorsUseCase:
    def __init__(
        self,
        engineering_snapshot_port: StrategicIndicatorsEngineeringIndicatorsSnapshotPort,
        production_snapshot_port: StrategicIndicatorsProductionIndicatorsSnapshotPort,
        commercial_snapshot_port: StrategicIndicatorsCommercialIndicatorsSnapshotPort,
        quality_snapshot_port: StrategicIndicatorsQualityIndicatorsSnapshotPort,
    ) -> None:
        self._engineering_snapshot_port = engineering_snapshot_port
        self._production_snapshot_port = production_snapshot_port
        self._commercial_snapshot_port = commercial_snapshot_port
        self._quality_snapshot_port = quality_snapshot_port

    def execute(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        department_id: str | None = None,
    ) -> GetStrategicIndicatorsResponse:
        raw_items: list[dict] = []
        errors: list[IndicatorFetchErrorResponse] = []

        self._collect_department_items(
            should_collect=department_id in (None, "", "engineering"),
            department_id="engineering",
            source="engineering_provider",
            fetcher=lambda: self._engineering_snapshot_port.get_engineering_indicators_snapshot(
                start_date=start_date,
                end_date=end_date,
            ),
            items=raw_items,
            errors=errors,
        )

        self._collect_department_items(
            should_collect=department_id in (None, "", "production"),
            department_id="production",
            source="production_provider",
            fetcher=lambda: self._production_snapshot_port.get_production_indicators_snapshot(
                start_date=start_date,
                end_date=end_date,
            ),
            items=raw_items,
            errors=errors,
        )

        self._collect_department_items(
            should_collect=department_id in (None, "", "commercial"),
            department_id="commercial",
            source="commercial_provider",
            fetcher=lambda: self._commercial_snapshot_port.get_commercial_indicators_snapshot(
                start_date=start_date,
                end_date=end_date,
            ),
            items=raw_items,
            errors=errors,
        )

        self._collect_department_items(
            should_collect=department_id in (None, "", "quality"),
            department_id="quality",
            source="quality_provider",
            fetcher=lambda: self._quality_snapshot_port.get_quality_indicators_snapshot(
                start_date=start_date,
                end_date=end_date,
            ),
            items=raw_items,
            errors=errors,
        )

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
                for item in raw_items
            ],
            errors=errors,
        )

    def _collect_department_items(
        self,
        *,
        should_collect: bool,
        department_id: str,
        source: str,
        fetcher,
        items: list[dict],
        errors: list[IndicatorFetchErrorResponse],
    ) -> None:
        if not should_collect:
            return

        try:
            result = fetcher()

            if isinstance(result, dict):
                for item in result.get("items", []):
                    items.append(item)

                for error in result.get("errors", []):
                    errors.append(
                        IndicatorFetchErrorResponse(
                            department_id=error["department_id"],
                            source=error["source"],
                            message=error["message"],
                        )
                    )
                return

            items.extend(result)

        except Exception as exc:
            errors.append(
                IndicatorFetchErrorResponse(
                    department_id=department_id,
                    source=source,
                    message=str(exc),
                )
            )