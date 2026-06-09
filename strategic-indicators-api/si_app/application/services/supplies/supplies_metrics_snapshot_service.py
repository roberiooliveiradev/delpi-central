from __future__ import annotations

from dataclasses import dataclass, field

from si_app.application.services.supplies.supplies_metrics_helpers import (
    build_cpv_payload,
    build_inventory_turnover_payload,
    build_otd_payload,
    build_stock_value_payload,
    build_turnover_raw_from_cpv,
)
from si_app.application.services.strategic_indicators.period_resolution import (
    ResolvedPeriod,
)
from si_app.infrastructure.gateways.delpi_financial_gateway import DelpiFinancialGateway
from si_app.infrastructure.gateways.delpi_supplies_gateway import DelpiSuppliesGateway
from si_app.shared.branch_filter import effective_query_branch
from si_app.shared.goal_scope import BRANCH_UNIT_CODES


@dataclass(frozen=True)
class SuppliesMetricsSnapshot:
    branch: str | None
    start_date: str | None
    end_date: str | None
    cpv_pct: float
    inventory_turnover_months: float
    otd_pct: float
    stock_value: float
    negotiation_savings_by_branch: dict[str, float | None] = field(default_factory=dict)


class SuppliesMetricsSnapshotService:
    def __init__(
        self,
        *,
        supplies_gateway: DelpiSuppliesGateway,
        financial_gateway: DelpiFinancialGateway,
    ) -> None:
        self._supplies_gateway = supplies_gateway
        self._financial_gateway = financial_gateway
        self._cache: dict[
            tuple[str | None, str | None, str | None],
            SuppliesMetricsSnapshot,
        ] = {}

    def get_snapshot(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        branch: str | None = None,
    ) -> SuppliesMetricsSnapshot:
        effective_branch = effective_query_branch(branch)
        key = (effective_branch, start_date, end_date)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        snapshot = self._build_snapshot(
            start_date=start_date,
            end_date=end_date,
            branch=effective_branch,
        )
        self._cache[key] = snapshot
        return snapshot

    def get_snapshot_series(
        self,
        *,
        periods: list[ResolvedPeriod],
        branch: str | None = None,
    ) -> dict[str, SuppliesMetricsSnapshot]:
        result: dict[str, SuppliesMetricsSnapshot] = {}

        effective_branch = effective_query_branch(branch)

        for period in periods:
            key = (effective_branch, period.start_date, period.end_date)
            cached = self._cache.get(key)
            if cached is not None:
                result[period.competence] = cached
                continue

            snapshot = self._build_snapshot(
                start_date=period.start_date,
                end_date=period.end_date,
                branch=effective_branch,
            )
            self._cache[key] = snapshot
            result[period.competence] = snapshot

        return result

    def _build_snapshot(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        branch: str | None,
    ) -> SuppliesMetricsSnapshot:
        cpv_raw = self._supplies_gateway.fetch_cpv_raw(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )
        rol_data = self._financial_gateway.get_rol(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )
        cpv_result = build_cpv_payload(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
            cpv_raw=cpv_raw,
            rol_data=rol_data,
        )

        stock_raw = self._supplies_gateway.fetch_stock_value_raw(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )
        turnover_raw = build_turnover_raw_from_cpv(
            cpv_raw=cpv_raw,
            start_date=start_date,
            end_date=end_date,
        )
        inventory_turnover_result = build_inventory_turnover_payload(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
            location=None,
            turnover_raw=turnover_raw,
            stock_raw=stock_raw,
            strict_idd_period=False,
        )

        otd_raw = self._supplies_gateway.fetch_otd_raw(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )
        otd_result = build_otd_payload(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
            otd_raw=otd_raw,
        )

        stock_value_result = build_stock_value_payload(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
            location=None,
            stock_raw=stock_raw,
        )

        cpv_summary = cpv_result.get("summary", {})
        inventory_turnover_summary = inventory_turnover_result.get("summary", {})
        otd_summary = otd_result.get("summary", {})
        stock_value_summary = stock_value_result.get("summary", {})

        return SuppliesMetricsSnapshot(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
            cpv_pct=self._to_float(cpv_summary.get("cpv_percentage")),
            inventory_turnover_months=self._to_float(
                inventory_turnover_summary.get("inventory_turnover_months")
            ),
            otd_pct=self._to_float(otd_summary.get("otd_percentage")),
            stock_value=self._to_float(stock_value_summary.get("total_stock_value")),
            negotiation_savings_by_branch=self._load_negotiation_savings_by_branch(
                start_date=start_date,
                end_date=end_date,
            ),
        )

    def _load_negotiation_savings_by_branch(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
    ) -> dict[str, float | None]:
        empty: dict[str, float | None] = {
            branch_code: None for branch_code in BRANCH_UNIT_CODES
        }

        try:
            payload = self._supplies_gateway.fetch_negotiation_savings_summary(
                start_date=start_date,
                end_date=end_date,
            )
        except Exception:
            return empty

        by_branch = dict(empty)

        for item in payload.get("branches") or []:
            branch_code = str(item.get("branch") or "").strip()
            if not branch_code:
                continue

            raw_total = item.get("total_savings")
            by_branch[branch_code] = (
                round(float(raw_total), 2) if raw_total is not None else None
            )

        return by_branch

    def _to_float(self, value) -> float:
        if value is None:
            return 0.0
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
