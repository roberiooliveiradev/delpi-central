from __future__ import annotations

from si_app.application.services.production.production_metrics_snapshot_service import (
    ProductionMetricsSnapshotService,
)
from si_app.application.services.strategic_indicators.period_resolution import (
    ResolvedPeriod,
)
from si_app.domain.ports.strategic_indicators.production_indicators_snapshot_port import (
    StrategicIndicatorsProductionIndicatorsSnapshotPort,
)
from si_app.shared.branch_filter import effective_query_branch
from si_app.shared.goal_scope import BRANCH_UNIT_CODES


class ProductionIndicatorsSnapshotProvider(
    StrategicIndicatorsProductionIndicatorsSnapshotPort,
):
    def __init__(
        self,
        *,
        production_metrics_snapshot_service: ProductionMetricsSnapshotService,
    ) -> None:
        self._production_metrics_snapshot_service = production_metrics_snapshot_service

    def get_production_indicators_snapshot(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
    ) -> dict:
        items: list[dict] = []
        errors: list[dict] = []

        try:
            snapshot = self._resolve_snapshot(
                branch=branch,
                start_date=start_date,
                end_date=end_date,
            )
        except Exception as exc:
            scope = branch or "consolidated"
            return {
                "items": [],
                "errors": [
                    {
                        "department_id": "production",
                        "source": f"production_snapshot_{scope}",
                        "message": str(exc),
                    }
                ],
            }

        self._collect_indicator(
            builder=lambda: self._build_measurement(
                indicator_id="production-direct-labor",
                source="production_direct_labor",
                snapshot=snapshot,
                value_getter=lambda item: item.direct_labor_cost_pct,
            ),
            department_id="production",
            source="production_direct_labor",
            items=items,
            errors=errors,
        )

        self._collect_indicator(
            builder=lambda: self._build_measurement(
                indicator_id="production-costs",
                source="production_cost",
                snapshot=snapshot,
                value_getter=lambda item: item.production_cost_pct,
            ),
            department_id="production",
            source="production_cost",
            items=items,
            errors=errors,
        )

        self._collect_indicator(
            builder=lambda: self._build_measurement(
                indicator_id="production-depreciation",
                source="production_depreciation",
                snapshot=snapshot,
                value_getter=lambda item: item.depreciation_pct,
            ),
            department_id="production",
            source="production_depreciation",
            items=items,
            errors=errors,
        )

        self._collect_indicator(
            builder=lambda: self._build_measurement(
                indicator_id="production-oee",
                source="production_oee",
                snapshot=snapshot,
                value_getter=lambda item: item.oee_pct,
            ),
            department_id="production",
            source="production_oee",
            items=items,
            errors=errors,
        )

        self._collect_indicator(
            builder=lambda: self._build_measurement(
                indicator_id="production-otd",
                source="production_otd",
                snapshot=snapshot,
                value_getter=lambda item: item.otd_pct,
            ),
            department_id="production",
            source="production_otd",
            items=items,
            errors=errors,
        )

        return {
            "items": items,
            "errors": errors,
        }

    def get_production_indicators_snapshot_series(
        self,
        *,
        periods: list[ResolvedPeriod],
        branch: str | None = None,
    ) -> dict[str, dict]:
        try:
            snapshots = self._production_metrics_snapshot_service.get_snapshot_series(
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
                            "department_id": "production",
                            "source": f"production_snapshot_{scope}",
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

            result[period.competence] = self._map_snapshot_to_result(snapshot=snapshot)

        return result

    def _map_snapshot_to_result(self, *, snapshot) -> dict:
        items: list[dict] = []
        errors: list[dict] = []

        self._collect_indicator(
            builder=lambda: self._build_measurement(
                indicator_id="production-direct-labor",
                source="production_direct_labor",
                snapshot=snapshot,
                value_getter=lambda item: item.direct_labor_cost_pct,
            ),
            department_id="production",
            source="production_direct_labor",
            items=items,
            errors=errors,
        )

        self._collect_indicator(
            builder=lambda: self._build_measurement(
                indicator_id="production-costs",
                source="production_cost",
                snapshot=snapshot,
                value_getter=lambda item: item.production_cost_pct,
            ),
            department_id="production",
            source="production_cost",
            items=items,
            errors=errors,
        )

        self._collect_indicator(
            builder=lambda: self._build_measurement(
                indicator_id="production-depreciation",
                source="production_depreciation",
                snapshot=snapshot,
                value_getter=lambda item: item.depreciation_pct,
            ),
            department_id="production",
            source="production_depreciation",
            items=items,
            errors=errors,
        )

        self._collect_indicator(
            builder=lambda: self._build_measurement(
                indicator_id="production-oee",
                source="production_oee",
                snapshot=snapshot,
                value_getter=lambda item: item.oee_pct,
            ),
            department_id="production",
            source="production_oee",
            items=items,
            errors=errors,
        )

        self._collect_indicator(
            builder=lambda: self._build_measurement(
                indicator_id="production-otd",
                source="production_otd",
                snapshot=snapshot,
                value_getter=lambda item: item.otd_pct,
            ),
            department_id="production",
            source="production_otd",
            items=items,
            errors=errors,
        )

        return {
            "items": items,
            "errors": errors,
        }

    def _resolve_snapshot(
        self,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ):
        effective_branch = effective_query_branch(branch)
        if effective_branch:
            return self._production_metrics_snapshot_service.get_unit_snapshot(
                branch=effective_branch,
                start_date=start_date,
                end_date=end_date,
            )

        return self._production_metrics_snapshot_service.get_consolidated_snapshot(
            start_date=start_date,
            end_date=end_date,
        )

    def _collect_indicator(
        self,
        *,
        builder,
        department_id: str,
        source: str,
        items: list[dict],
        errors: list[dict],
    ) -> None:
        try:
            items.append(builder())
        except Exception as exc:
            errors.append(
                {
                    "department_id": department_id,
                    "source": source,
                    "message": str(exc),
                }
            )

    def _build_measurement(
        self,
        *,
        indicator_id: str,
        source: str,
        snapshot,
        value_getter,
    ) -> dict:
        value = value_getter(snapshot)
        normalized_value = float(value) if value is not None else None

        return {
            "department_id": "production",
            "indicator_id": indicator_id,
            "value": normalized_value,
            "source": source,
            "unit_values": self._build_unit_values(
                snapshot=snapshot,
                value_getter=value_getter,
                consolidated_value=normalized_value,
            ),
        }

    def _build_unit_values(
        self,
        *,
        snapshot,
        value_getter,
        consolidated_value: float | None,
    ) -> dict[str, float | None]:
        if snapshot.branch:
            return {snapshot.branch: consolidated_value}

        unit_values: dict[str, float | None] = {
            "consolidated": consolidated_value,
        }
        start_date = snapshot.start_date
        end_date = snapshot.end_date

        for branch_code in BRANCH_UNIT_CODES:
            try:
                unit_snapshot = (
                    self._production_metrics_snapshot_service.get_unit_snapshot(
                        branch=branch_code,
                        start_date=start_date,
                        end_date=end_date,
                    )
                )
                branch_raw = value_getter(unit_snapshot)
                unit_values[branch_code] = (
                    float(branch_raw) if branch_raw is not None else None
                )
            except Exception:
                unit_values[branch_code] = None

        return unit_values