from __future__ import annotations

from app.application.dto.lmp.list_lmp_request import ListLMPRequest
from app.application.dto.transforma_mais.process_summary_request import ProcessSummaryRequest
from app.application.use_cases.lmp.list_lmp_dashboard_use_case import ListLMPDashboardUseCase
from app.application.use_cases.transforma_mais.get_process_summary_use_case import (
    GetProcessSummaryUseCase,
)
from app.domain.ports.strategic_indicators.engineering_indicators_snapshot_port import (
    StrategicIndicatorsEngineeringIndicatorsSnapshotPort,
)


class EngineeringIndicatorsSnapshotProvider(
    StrategicIndicatorsEngineeringIndicatorsSnapshotPort,
):
    def __init__(
        self,
        *,
        lmp_dashboard_use_case: ListLMPDashboardUseCase,
        transforma_mais_summary_use_case: GetProcessSummaryUseCase,
    ) -> None:
        self._lmp_dashboard_use_case = lmp_dashboard_use_case
        self._transforma_mais_summary_use_case = transforma_mais_summary_use_case

    def get_engineering_indicators_snapshot(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict:
        items: list[dict] = []
        errors: list[dict] = []

        self._collect_indicator(
            builder=lambda: self._build_lmp_projects_on_time_indicator(
                start_date=start_date,
                end_date=end_date,
            ),
            department_id="engineering",
            source="lmp",
            items=items,
            errors=errors,
        )

        self._collect_indicator(
            builder=lambda: self._build_transforma_mais_financial_gain_indicator(
                start_date=start_date,
                end_date=end_date,
            ),
            department_id="engineering",
            source="transforma_mais",
            items=items,
            errors=errors,
        )

        return {
            "items": items,
            "errors": errors,
        }

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

    def _build_lmp_projects_on_time_indicator(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
    ) -> dict:
        request = ListLMPRequest(
            date_start=start_date,
            date_end=end_date,
            branch=None,
            page=None,
            page_size=None,
        )

        result = self._lmp_dashboard_use_case.execute(request, status_filter="Todos")
        summary = result.get("summary", {})

        value = float(summary.get("percent_dentro_prazo", 0))
        goal = 95.0
        gap = round(goal - value, 2)
        score = self._score_higher_is_better(value=value, goal=goal)

        return {
            "department_id": "engineering",
            "department_name": "Engenharia",
            "indicator_id": "engineering-projects-on-time",
            "indicator_name": "% de Projetos Concluídos no Prazo",
            "weight_pct": 60,
            "goal_2026": "95%",
            "scope_type": "per_unit",
            "value": value,
            "score": score,
            "gap": gap,
            "trend": "up" if value >= goal else "stable",
            "classification": self._classify_score(score),
            "source": "lmp",
        }

    def _build_transforma_mais_financial_gain_indicator(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
    ) -> dict:
        request = ProcessSummaryRequest(
            filial_id=None,
            start_date=start_date,
            end_date=end_date,
        )

        summary = self._transforma_mais_summary_use_case.execute(request)
        payload = summary.to_dict() if hasattr(summary, "to_dict") else summary

        value = self._extract_financial_gain_value(payload)
        goal = 15000.0
        gap = round(goal - value, 2)
        score = self._score_higher_is_better(value=value, goal=goal)

        return {
            "department_id": "engineering",
            "department_name": "Engenharia",
            "indicator_id": "engineering-transforma-plus",
            "indicator_name": "Ganhos Financeiros do TRANSFORMA+ DELPI",
            "weight_pct": 40,
            "goal_2026": "R$ 15.000/mês",
            "scope_type": "per_unit",
            "value": value,
            "score": score,
            "gap": gap,
            "trend": "up" if value >= goal else "stable",
            "classification": self._classify_score(score),
            "source": "transforma_mais",
        }

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

    def _score_higher_is_better(self, *, value: float, goal: float) -> float:
        if goal <= 0:
            return 0.0

        ratio = value / goal
        score = ratio * 10
        return round(min(score, 10.0), 2)

    def _classify_score(self, score: float) -> str:
        if score >= 9:
            return "Excelência Integrada"
        if score >= 8:
            return "Alto Desempenho"
        if score >= 7:
            return "Satisfatório com Alertas"
        if score >= 6:
            return "Regular, Exige Ação"
        return "Crítico"