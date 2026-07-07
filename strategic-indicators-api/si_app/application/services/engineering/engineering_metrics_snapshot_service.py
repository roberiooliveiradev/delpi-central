from __future__ import annotations

from dataclasses import dataclass

from si_app.application.services.engineering.engineering_metrics_helpers import (
    resolve_lmp_dashboard_summary,
)
from si_app.application.services.strategic_indicators.period_resolution import (
    ResolvedPeriod,
    clamp_resolved_period_to_elapsed,
    resolve_period,
)
from si_app.infrastructure.gateways.delpi_engineering_gateway import DelpiEngineeringGateway
from si_app.shared.branch_filter import effective_query_branch


@dataclass(frozen=True)
class EngineeringMetricsSnapshot:
    start_date: str | None
    end_date: str | None
    lmp_projects_on_time_pct: float | None
    transforma_mais_financial_gain: float | None
    requested_branch: str | None = None


class EngineeringMetricsSnapshotService:
    def __init__(
        self,
        *,
        engineering_gateway: DelpiEngineeringGateway,
    ) -> None:
        self._engineering_gateway = engineering_gateway
        self._cache: dict[
            tuple[str | None, str | None, str | None],
            EngineeringMetricsSnapshot,
        ] = {}

    def get_snapshot(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        branch: str | None = None,
    ) -> EngineeringMetricsSnapshot:
        effective_branch = effective_query_branch(branch)
        key = (start_date, end_date, effective_branch)
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
    ) -> dict[str, EngineeringMetricsSnapshot]:
        result: dict[str, EngineeringMetricsSnapshot] = {}

        effective_branch = effective_query_branch(branch)

        for period in periods:
            key = (period.start_date, period.end_date, effective_branch)
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
    ) -> EngineeringMetricsSnapshot:
        requested_period = resolve_period(
            competence=None,
            start_date=start_date,
            end_date=end_date,
        )
        effective_period, _entirely_future = clamp_resolved_period_to_elapsed(
            requested_period
        )
        query_start = effective_period.start_date
        query_end = effective_period.end_date

        lmp_summary = resolve_lmp_dashboard_summary(
            gateway=self._engineering_gateway,
            date_start=query_start,
            date_end=query_end,
            branch=branch,
        )

        lmp_projects_on_time_pct = self._to_float(
            lmp_summary.get("percent_dentro_prazo")
        )

        transforma_summary = self._engineering_gateway.get_transforma_mais_summary(
            filial_id=branch,
            start_date=query_start,
            end_date=query_end,
        )
        transforma_mais_financial_gain = self._extract_financial_gain_value(
            transforma_summary
        )

        snapshot = EngineeringMetricsSnapshot(
            start_date=start_date,
            end_date=end_date,
            lmp_projects_on_time_pct=(
                round(lmp_projects_on_time_pct, 2)
                if lmp_projects_on_time_pct is not None
                else None
            ),
            transforma_mais_financial_gain=(
                round(transforma_mais_financial_gain, 2)
                if transforma_mais_financial_gain is not None
                else None
            ),
            requested_branch=branch,
        )
        self._cache[(start_date, end_date, branch)] = snapshot
        return snapshot

    def _extract_financial_gain_value(self, payload: dict) -> float | None:
        data = payload.get("data", payload)

        value = data.get("total_gross_savings_in_period")
        direct_value = self._to_float(value)
        if direct_value is not None:
            return direct_value

        monthly_breakdown = data.get("monthly_breakdown", [])
        if monthly_breakdown:
            values: list[float] = []

            for item in monthly_breakdown:
                monthly_value = self._to_float(item.get("gross_savings_month"))
                if monthly_value is not None:
                    values.append(monthly_value)

            if values:
                return sum(values)

        return None

    def _to_float(self, value) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
