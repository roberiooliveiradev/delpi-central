from __future__ import annotations

from app.application.dto.strategic_indicators.get_executive_summary_response import (
    ExecutiveSummaryAlertResponse,
    ExecutiveSummaryDepartmentResponse,
    ExecutiveSummaryVariationResponse,
    GetStrategicIndicatorsExecutiveSummaryResponse,
)
from app.domain.ports.strategic_indicators.alerts_summary_port import (
    StrategicIndicatorsAlertsSummaryPort,
)
from app.domain.ports.strategic_indicators.department_snapshot_port import (
    StrategicIndicatorsDepartmentSnapshotPort,
)
from app.domain.ports.strategic_indicators.igd_snapshot_port import (
    StrategicIndicatorsIgdSnapshotPort,
)
from app.domain.ports.strategic_indicators.summary_settings_port import (
    StrategicIndicatorsSummarySettingsPort,
)


class GetStrategicIndicatorsExecutiveSummaryUseCase:
    def __init__(
        self,
        settings_port: StrategicIndicatorsSummarySettingsPort,
        department_snapshot_port: StrategicIndicatorsDepartmentSnapshotPort,
        igd_snapshot_port: StrategicIndicatorsIgdSnapshotPort,
        alerts_summary_port: StrategicIndicatorsAlertsSummaryPort,
    ) -> None:
        self._settings_port = settings_port
        self._department_snapshot_port = department_snapshot_port
        self._igd_snapshot_port = igd_snapshot_port
        self._alerts_summary_port = alerts_summary_port

    def execute(self) -> GetStrategicIndicatorsExecutiveSummaryResponse:
        settings = self._settings_port.get_summary_settings()
        igd_snapshot = self._igd_snapshot_port.get_igd_snapshot()
        department_snapshots = self._department_snapshot_port.get_department_snapshots()
        alerts_summary = self._alerts_summary_port.get_alerts_summary()

        weights_items = settings.get("weights", {}).get("items", [])
        goals_items = settings.get("goals", {}).get("items", [])
        indicators_items = settings.get("indicators", {}).get("items", [])

        goals_map = {
            item["department_id"]: item["headline_goal"]
            for item in goals_items
            if item.get("department_id") and item.get("headline_goal")
        }

        indicators_map = {
            item["department_id"]: item
            for item in indicators_items
            if item.get("department_id")
        }

        snapshot_map = {
            item["department_id"]: item
            for item in department_snapshots
            if item.get("department_id")
        }

        departments: list[ExecutiveSummaryDepartmentResponse] = []

        for weight_item in weights_items:
            department_id = weight_item["department_id"]
            snapshot = snapshot_map.get(department_id)
            indicator_catalog = indicators_map.get(department_id, {})

            if snapshot is None:
                continue

            score = float(snapshot.get("score", 0))
            weight_pct = int(weight_item["weight_pct"])
            contribution = round(score * (weight_pct / 100), 3)

            key_indicators = [
                indicator.get("name", "")
                for indicator in indicator_catalog.get("indicators", [])[:3]
                if indicator.get("name")
            ]

            departments.append(
                ExecutiveSummaryDepartmentResponse(
                    id=department_id,
                    name=weight_item["department_name"],
                    short_name=snapshot.get(
                        "short_name",
                        indicator_catalog.get("short_name", ""),
                    ),
                    weight_pct=weight_pct,
                    score=score,
                    contribution=contribution,
                    trend=snapshot.get("trend", "stable"),
                    strategic_summary=snapshot.get(
                        "strategic_summary",
                        indicator_catalog.get("strategic_summary", ""),
                    ),
                    key_indicators=key_indicators,
                    executive_goal=goals_map.get(department_id, ""),
                )
            )

        variation = igd_snapshot.get("variation", {})

        return GetStrategicIndicatorsExecutiveSummaryResponse(
            competence=igd_snapshot.get("competence", ""),
            igd=float(igd_snapshot.get("igd", 0)),
            igd_exact=float(igd_snapshot.get("igd_exact", 0)),
            classification=igd_snapshot.get("classification", ""),
            variation=ExecutiveSummaryVariationResponse(
                value=float(variation.get("value", 0)),
                direction=variation.get("direction", "stable"),
                vs_label=variation.get("vs_label", "vs período anterior"),
            ),
            departments=departments,
            alerts_summary=[
                ExecutiveSummaryAlertResponse(
                    title=item.get("title", ""),
                    severity=item.get("severity", "low"),
                    impact=item.get("impact", ""),
                    recommendation=item.get("recommendation", ""),
                )
                for item in alerts_summary
            ],
        )