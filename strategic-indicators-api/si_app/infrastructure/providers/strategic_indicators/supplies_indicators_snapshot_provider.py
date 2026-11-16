from __future__ import annotations

from si_app.application.services.supplies.supplies_metrics_snapshot_service import (
    SuppliesMetricsSnapshotService,
)
from si_app.application.services.strategic_indicators.period_resolution import (
    ResolvedPeriod,
)
from si_app.domain.ports.strategic_indicators.supplies_indicators_snapshot_port import (
    StrategicIndicatorsSuppliesIndicatorsSnapshotPort,
)
from si_app.shared.goal_scope import BRANCH_UNIT_CODES
from si_app.shared.numeric_parsing import to_optional_float

class SuppliesIndicatorsSnapshotProvider(
    StrategicIndicatorsSuppliesIndicatorsSnapshotPort,
):
    def __init__(
        self,
        *,
        supplies_metrics_snapshot_service: SuppliesMetricsSnapshotService,
    ) -> None:
        self._supplies_metrics_snapshot_service = supplies_metrics_snapshot_service

    def get_supplies_indicators_snapshot(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
    ) -> dict:
        try:
            snapshot = self._supplies_metrics_snapshot_service.get_snapshot(
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
                        "department_id": "supplies",
                        "source": f"supplies_snapshot_{scope}",
                        "message": str(exc),
                    }
                ],
            }

        return self._map_snapshot_to_result(snapshot=snapshot)

    def get_supplies_indicators_snapshot_series(
        self,
        *,
        periods: list[ResolvedPeriod],
        branch: str | None = None,
    ) -> dict[str, dict]:
        try:
            snapshots = self._supplies_metrics_snapshot_service.get_snapshot_series(
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
                            "department_id": "supplies",
                            "source": f"supplies_snapshot_{scope}",
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
        return {
            "items": [
                self._build_indicator_measurement(
                    snapshot=snapshot,
                    indicator_id="supplies-cpv",
                    source="supplies_cpv",
                    value=snapshot.cpv_pct,
                ),
                self._build_indicator_measurement(
                    snapshot=snapshot,
                    indicator_id="supplies-stock-turnover",
                    source="supplies_inventory_turnover",
                    value=snapshot.inventory_turnover_times,
                ),
                self._build_indicator_measurement(
                    snapshot=snapshot,
                    indicator_id="supplies-otd",
                    source="supplies_otd",
                    value=snapshot.otd_pct,
                ),
                self._build_indicator_measurement(
                    snapshot=snapshot,
                    indicator_id="supplies-stock-value",
                    source="supplies_stock_value",
                    value=snapshot.stock_value,
                ),
                self._build_negotiation_savings_measurement(snapshot=snapshot),
                self._build_sc_pc_conversion_measurement(snapshot=snapshot),
            ],
            "errors": [],
        }

    @staticmethod
    def _conversion_average(values: dict[str, int] | None) -> float | None:
        if values is None:
            return None
        count = values.get("converted_requests", 0)
        if count <= 0:
            return None
        return round(values["sum_conversion_days"] / count, 2)

    def _build_sc_pc_conversion_measurement(self, *, snapshot) -> dict:
        """Weighted by converted SC count, never average filial averages."""
        counts = snapshot.sc_pc_conversion_by_branch or {}
        unit_values = {
            branch: self._conversion_average(counts.get(branch))
            for branch in BRANCH_UNIT_CODES
        }
        valid = [row for row in counts.values() if row is not None]
        # Do not claim consolidated value when either branch is unavailable.
        complete = all(counts.get(branch) is not None for branch in BRANCH_UNIT_CODES)
        if snapshot.branch in BRANCH_UNIT_CODES:
            value = unit_values.get(snapshot.branch)
        elif complete and valid:
            total_count = sum(row["converted_requests"] for row in valid)
            total_days = sum(row["sum_conversion_days"] for row in valid)
            value = round(total_days / total_count, 2) if total_count else None
        else:
            value = None
        if snapshot.branch is None:
            unit_values["consolidated"] = value
        return {
            "department_id": "supplies",
            "indicator_id": "supplies-sc-pc-conversion-days",
            "value": value,
            "source": "supplies_sc_pc_conversion",
            "unit_values": unit_values,
        }

    def _build_negotiation_savings_measurement(self, *, snapshot) -> dict:
        unit_values = dict(snapshot.negotiation_savings_by_branch or {})
        consolidated_value = self._sum_branch_values(unit_values)

        return {
            "department_id": "supplies",
            "indicator_id": "supplies-negotiation-savings",
            "value": consolidated_value,
            "source": "supplies_negotiation_savings",
            "unit_values": unit_values,
        }

    @staticmethod
    def _sum_branch_values(unit_values: dict[str, float | None]) -> float | None:
        values = [value for value in unit_values.values() if value is not None]
        if not values:
            return None
        return round(sum(values), 2)

    def _build_indicator_measurement(
        self,
        *,
        snapshot,
        indicator_id: str,
        source: str,
        value: float,
    ) -> dict:
        return {
            "department_id": "supplies",
            "indicator_id": indicator_id,
            "value": value,
            "source": source,
            "unit_values": self._build_unit_values(
                snapshot=snapshot,
                consolidated_value=value,
                value_attr=self._value_attr_for_indicator(indicator_id),
            ),
        }

    @staticmethod
    def _value_attr_for_indicator(indicator_id: str) -> str:
        mapping = {
            "supplies-cpv": "cpv_pct",
            "supplies-stock-turnover": "inventory_turnover_times",
            "supplies-otd": "otd_pct",
            "supplies-stock-value": "stock_value",
        }
        return mapping[indicator_id]

    def _build_unit_values(
        self,
        *,
        snapshot,
        consolidated_value: float,
        value_attr: str,
    ) -> dict[str, float | None]:
        if snapshot.branch:
            return {snapshot.branch: consolidated_value}

        unit_values: dict[str, float | None] = {
            "consolidated": consolidated_value,
        }

        for branch_code in BRANCH_UNIT_CODES:
            try:
                unit_snapshot = self._supplies_metrics_snapshot_service.get_snapshot(
                    start_date=snapshot.start_date,
                    end_date=snapshot.end_date,
                    branch=branch_code,
                )
                branch_value = getattr(unit_snapshot, value_attr, None)
                unit_values[branch_code] = (
                    to_optional_float(branch_value)
                )
            except Exception:
                unit_values[branch_code] = None

        return unit_values