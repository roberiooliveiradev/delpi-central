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
            builder=lambda: self._build_lmp_projects_on_time_measurement(
                start_date=start_date,
                end_date=end_date,
            ),
            department_id="engineering",
            source="lmp",
            items=items,
            errors=errors,
        )

        self._collect_indicator(
            builder=lambda: self._build_transforma_mais_financial_gain_measurement(
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

    def _build_lmp_projects_on_time_measurement(
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

        return {
            "department_id": "engineering",
            "indicator_id": "engineering-projects-on-time",
            "value": value,
            "source": "lmp",
            "unit_values": None,
        }

    def _build_transforma_mais_financial_gain_measurement(
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

        return {
            "department_id": "engineering",
            "indicator_id": "engineering-transforma-plus",
            "value": value,
            "source": "transforma_mais",
            "unit_values": None,
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