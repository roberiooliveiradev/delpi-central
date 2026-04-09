from __future__ import annotations

from dataclasses import dataclass

from app.application.dto.lmp.list_lmp_request import ListLMPRequest
from app.application.dto.transforma_mais.process_summary_request import ProcessSummaryRequest
from app.application.use_cases.lmp.list_lmp_dashboard_use_case import (
    ListLMPDashboardUseCase,
)
from app.application.use_cases.transforma_mais.get_process_summary_use_case import (
    GetProcessSummaryUseCase,
)


@dataclass(frozen=True)
class EngineeringMetricsSnapshot:
    start_date: str | None
    end_date: str | None
    lmp_projects_on_time_pct: float
    transforma_mais_financial_gain: float


class EngineeringMetricsSnapshotService:
    def __init__(
        self,
        *,
        lmp_dashboard_use_case: ListLMPDashboardUseCase,
        transforma_mais_summary_use_case: GetProcessSummaryUseCase,
    ) -> None:
        self._lmp_dashboard_use_case = lmp_dashboard_use_case
        self._transforma_mais_summary_use_case = transforma_mais_summary_use_case
        self._cache: dict[tuple[str | None, str | None], EngineeringMetricsSnapshot] = {}

    def get_snapshot(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
    ) -> EngineeringMetricsSnapshot:
        key = (start_date, end_date)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        lmp_result = self._lmp_dashboard_use_case.execute(
            ListLMPRequest(
                date_start=start_date,
                date_end=end_date,
                branch=None,
                page=None,
                page_size=None,
            ),
            status_filter="Todos",
        )
        lmp_summary = lmp_result.get("summary", {})
        lmp_projects_on_time_pct = float(lmp_summary.get("percent_dentro_prazo", 0) or 0)

        transforma_summary = self._transforma_mais_summary_use_case.execute(
            ProcessSummaryRequest(
                filial_id=None,
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
            lmp_projects_on_time_pct=lmp_projects_on_time_pct,
            transforma_mais_financial_gain=transforma_mais_financial_gain,
        )
        self._cache[key] = snapshot
        return snapshot

    def _extract_financial_gain_value(self, payload: dict) -> float:
        data = payload.get("data", payload)

        value = data.get("total_gross_savings_in_period")
        if isinstance(value, (int, float)):
            return float(value)

        monthly_breakdown = data.get("monthly_breakdown", [])
        if monthly_breakdown:
            total = 0.0
            for item in monthly_breakdown:
                monthly_value = item.get("gross_savings_month")
                if isinstance(monthly_value, (int, float)):
                    total += float(monthly_value)
            return total

        return 0.0