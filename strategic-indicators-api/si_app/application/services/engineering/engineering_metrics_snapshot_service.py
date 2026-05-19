from __future__ import annotations

from dataclasses import dataclass

from si_app.application.dto.lmp.list_lmp_request import ListLMPRequest
from si_app.application.dto.transforma_mais.process_summary_request import ProcessSummaryRequest
from si_app.application.use_cases.lmp.get_lmp_dashboard_summary_use_case import (
    GetLMPDashboardSummaryUseCase,
)
from si_app.application.use_cases.strategic_indicators.period_resolution import (
    ResolvedPeriod,
)
from si_app.application.use_cases.transforma_mais.get_process_summary_use_case import (
    GetProcessSummaryUseCase,
)


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
        lmp_dashboard_summary_use_case: GetLMPDashboardSummaryUseCase,
        transforma_mais_summary_use_case: GetProcessSummaryUseCase,
    ) -> None:
        self._lmp_dashboard_summary_use_case = lmp_dashboard_summary_use_case
        self._transforma_mais_summary_use_case = transforma_mais_summary_use_case
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
        key = (start_date, end_date, branch)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        snapshot = self._build_snapshot(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
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

        for period in periods:
            key = (period.start_date, period.end_date, branch)
            cached = self._cache.get(key)
            if cached is not None:
                result[period.competence] = cached
                continue

            snapshot = self._build_snapshot(
                start_date=period.start_date,
                end_date=period.end_date,
                branch=branch,
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
        lmp_summary = self._lmp_dashboard_summary_use_case.execute(
            ListLMPRequest(
                date_start=start_date,
                date_end=end_date,
                branch=branch,
                page=None,
                page_size=None,
                include_qtd_pi=False,
            ),
            include_avg_lead_time=False,
        )

        lmp_projects_on_time_pct = self._to_float(
            lmp_summary.percent_dentro_prazo
        )

        transforma_summary = self._transforma_mais_summary_use_case.execute(
            ProcessSummaryRequest(
                filial_id=branch,
                start_date=start_date,
                end_date=end_date,
            )
        )
        payload = (
            transforma_summary.to_dict()
            if hasattr(transforma_summary, "to_dict")
            else transforma_summary
        )
        transforma_mais_financial_gain = self._extract_financial_gain_value(payload)

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