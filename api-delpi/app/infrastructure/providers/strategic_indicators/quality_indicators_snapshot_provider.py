from __future__ import annotations

from app.application.services.quality.quality_metrics_snapshot_service import (
    QualityMetricsSnapshotService,
)
from app.application.use_cases.strategic_indicators.period_resolution import (
    ResolvedPeriod,
)
from app.domain.ports.strategic_indicators.quality_indicators_snapshot_port import (
    StrategicIndicatorsQualityIndicatorsSnapshotPort,
)


class QualityIndicatorsSnapshotProvider(
    StrategicIndicatorsQualityIndicatorsSnapshotPort,
):
    def __init__(
        self,
        *,
        quality_metrics_snapshot_service: QualityMetricsSnapshotService,
    ) -> None:
        self._quality_metrics_snapshot_service = quality_metrics_snapshot_service

    def get_quality_indicators_snapshot(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
    ) -> dict:
        try:
            snapshot = self._quality_metrics_snapshot_service.get_snapshot(
                start_date=start_date,
                end_date=end_date,
                branch=branch,
            )
        except Exception as exc:
            scope = branch or "consolidated"
            return {
                "items": [],
                "errors": [
                    {
                        "department_id": "quality",
                        "source": f"quality_snapshot_{scope}",
                        "message": str(exc),
                    }
                ],
            }

        return self._map_snapshot_to_result(
            snapshot=snapshot,
            branch=branch,
        )

    def get_quality_indicators_snapshot_series(
        self,
        *,
        periods: list[ResolvedPeriod],
        branch: str | None = None,
    ) -> dict[str, dict]:
        try:
            snapshots = self._quality_metrics_snapshot_service.get_snapshot_series(
                periods=periods,
                branch=branch,
            )
        except Exception as exc:
            scope = branch or "consolidated"
            return {
                period.competence: {
                    "items": [],
                    "errors": [
                        {
                            "department_id": "quality",
                            "source": f"quality_snapshot_{scope}",
                            "message": str(exc),
                        }
                    ],
                }
                for period in periods
            }

        result: dict[str, dict] = {}

        for period in periods:
            snapshot = snapshots.get(period.competence)
            if snapshot is None:
                result[period.competence] = {"items": [], "errors": []}
                continue

            result[period.competence] = self._map_snapshot_to_result(
                snapshot=snapshot,
                branch=branch,
            )

        return result

    def _map_snapshot_to_result(
        self,
        *,
        snapshot,
        branch: str | None,
    ) -> dict:
        ppm_internal_unit_values = {
            item.branch: item.ppm_internal for item in snapshot.branches
        }
        ppm_external_unit_values = {
            item.branch: item.ppm_external for item in snapshot.branches
        }
        kaizen_ideas_unit_values = {
            item.branch: item.kaizen_ideas_avg for item in snapshot.branches
        }
        kaizen_financial_unit_values = {
            item.branch: item.kaizen_financial_gain for item in snapshot.branches
        }
        audit_5s_unit_values = {
            item.branch: item.audit_5s_score for item in snapshot.branches
        }

        return {
            "items": [
                {
                    "department_id": "quality",
                    "indicator_id": "quality-ppm-internal",
                    "value": self._resolve_indicator_value(
                        unit_values=ppm_internal_unit_values,
                        branch=branch,
                        default_value=0.0,
                    ),
                    "source": "quality_ppm_internal",
                    "unit_values": ppm_internal_unit_values,
                },
                {
                    "department_id": "quality",
                    "indicator_id": "quality-ppm-external",
                    "value": self._resolve_indicator_value(
                        unit_values=ppm_external_unit_values,
                        branch=branch,
                        default_value=0.0,
                    ),
                    "source": "quality_ppm_external",
                    "unit_values": ppm_external_unit_values,
                },
                {
                    "department_id": "quality",
                    "indicator_id": "quality-kaizen-ideas",
                    "value": self._resolve_indicator_value(
                        unit_values=kaizen_ideas_unit_values,
                        branch=branch,
                    ),
                    "source": "quality_kaizen_ideas",
                    "unit_values": kaizen_ideas_unit_values,
                },
                {
                    "department_id": "quality",
                    "indicator_id": "quality-kaizen-financial",
                    "value": self._resolve_indicator_value(
                        unit_values=kaizen_financial_unit_values,
                        branch=branch,
                    ),
                    "source": "quality_kaizen_financial",
                    "unit_values": kaizen_financial_unit_values,
                },
                {
                    "department_id": "quality",
                    "indicator_id": "quality-audit-5s",
                    "value": self._resolve_indicator_value(
                        unit_values=audit_5s_unit_values,
                        branch=branch,
                    ),
                    "source": "quality_audit_5s",
                    "unit_values": audit_5s_unit_values,
                },
            ],
            "errors": [],
        }

    def _resolve_indicator_value(
        self,
        *,
        unit_values: dict[str, float | None],
        branch: str | None,
        default_value: float | None = None,
    ) -> float | None:
        if branch:
            value = unit_values.get(branch)

            if value is None:
                return default_value

            return round(float(value), 2)

        values = [
            float(value)
            for value in unit_values.values()
            if value is not None
        ]

        if not values:
            return default_value

        return round(sum(values) / len(values), 2)