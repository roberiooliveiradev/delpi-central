from __future__ import annotations

from app.application.dto.strategic_indicators.get_executive_summary_response import (
    ExecutiveSummaryAlertResponse,
    ExecutiveSummaryDepartmentResponse,
    ExecutiveSummaryVariationResponse,
    GetStrategicIndicatorsExecutiveSummaryResponse,
)
from app.domain.ports.strategic_indicators.executive_summary_repository_port import (
    StrategicIndicatorsExecutiveSummaryRepositoryPort,
)


class GetStrategicIndicatorsExecutiveSummaryUseCase:
    def __init__(
        self,
        repository: StrategicIndicatorsExecutiveSummaryRepositoryPort,
    ) -> None:
        self._repository = repository

    def execute(self) -> GetStrategicIndicatorsExecutiveSummaryResponse:
        result = self._repository.get_executive_summary()

        variation = result.get("variation", {})

        return GetStrategicIndicatorsExecutiveSummaryResponse(
            competence=result.get("competence", ""),
            igd=float(result.get("igd", 0)),
            igd_exact=float(result.get("igd_exact", 0)),
            classification=result.get("classification", ""),
            variation=ExecutiveSummaryVariationResponse(
                value=float(variation.get("value", 0)),
                direction=variation.get("direction", "stable"),
                vs_label=variation.get("vs_label", "vs período anterior"),
            ),
            departments=[
                ExecutiveSummaryDepartmentResponse(
                    id=item["id"],
                    name=item["name"],
                    short_name=item["short_name"],
                    weight_pct=int(item["weight_pct"]),
                    score=float(item["score"]),
                    contribution=float(item["contribution"]),
                    trend=item.get("trend", "stable"),
                    strategic_summary=item.get("strategic_summary", ""),
                    key_indicators=list(item.get("key_indicators", [])),
                    executive_goal=item.get("executive_goal", ""),
                )
                for item in result.get("departments", [])
            ],
            alerts_summary=[
                ExecutiveSummaryAlertResponse(
                    title=item.get("title", ""),
                    severity=item.get("severity", "low"),
                    impact=item.get("impact", ""),
                    recommendation=item.get("recommendation", ""),
                )
                for item in result.get("alerts_summary", [])
            ],
        )