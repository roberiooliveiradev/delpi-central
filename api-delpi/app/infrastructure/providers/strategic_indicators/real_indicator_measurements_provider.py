from __future__ import annotations

from app.application.dto.strategic_indicators.catalog_models import (
    StrategicIndicatorMeasuredValue,
)
from app.domain.ports.strategic_indicators.indicator_measurements_port import (
    StrategicIndicatorsIndicatorMeasurementsPort,
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


class RealStrategicIndicatorsMeasurementsProvider(
    StrategicIndicatorsIndicatorMeasurementsPort,
):
    def __init__(
        self,
        *,
        engineering_snapshot_port: StrategicIndicatorsEngineeringIndicatorsSnapshotPort,
        production_snapshot_port: StrategicIndicatorsProductionIndicatorsSnapshotPort,
        commercial_snapshot_port: StrategicIndicatorsCommercialIndicatorsSnapshotPort,
        quality_snapshot_port: StrategicIndicatorsQualityIndicatorsSnapshotPort,
    ) -> None:
        self._engineering_snapshot_port = engineering_snapshot_port
        self._production_snapshot_port = production_snapshot_port
        self._commercial_snapshot_port = commercial_snapshot_port
        self._quality_snapshot_port = quality_snapshot_port

    def get_indicator_measurements(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        department_id: str | None = None,
    ) -> tuple[list[StrategicIndicatorMeasuredValue], list[dict]]:
        items: list[StrategicIndicatorMeasuredValue] = []
        errors: list[dict] = []

        self._collect(
            should_collect=department_id in (None, "", "engineering"),
            fetcher=lambda: self._engineering_snapshot_port.get_engineering_indicators_snapshot(
                start_date=start_date,
                end_date=end_date,
            ),
            items=items,
            errors=errors,
        )

        self._collect(
            should_collect=department_id in (None, "", "production"),
            fetcher=lambda: self._production_snapshot_port.get_production_indicators_snapshot(
                start_date=start_date,
                end_date=end_date,
            ),
            items=items,
            errors=errors,
        )

        self._collect(
            should_collect=department_id in (None, "", "commercial"),
            fetcher=lambda: self._commercial_snapshot_port.get_commercial_indicators_snapshot(
                start_date=start_date,
                end_date=end_date,
            ),
            items=items,
            errors=errors,
        )

        self._collect(
            should_collect=department_id in (None, "", "quality"),
            fetcher=lambda: self._quality_snapshot_port.get_quality_indicators_snapshot(
                start_date=start_date,
                end_date=end_date,
            ),
            items=items,
            errors=errors,
        )

        return items, errors

    def _collect(
        self,
        *,
        should_collect: bool,
        fetcher,
        items: list[StrategicIndicatorMeasuredValue],
        errors: list[dict],
    ) -> None:
        if not should_collect:
            return

        result = fetcher()
        for raw in result.get("items", []):
            items.append(
                StrategicIndicatorMeasuredValue(
                    indicator_id=raw["indicator_id"],
                    department_id=raw["department_id"],
                    value=float(raw["value"]),
                    source=raw["source"],
                    unit_values=raw.get("unit_values"),
                )
            )

        errors.extend(result.get("errors", []))