from __future__ import annotations

from app.application.dto.transforma_mais.process_request import ProcessRequest
from app.application.dto.transforma_mais.process_summary_request import ProcessSummaryRequest
from app.application.dto.transforma_mais.process_summary_response import (
    MonthlySummaryItem,
    ProcessSummaryResponse,
    RangeSummary,
)
from app.domain.entities.transforma_mais.process import Process
from app.domain.ports.transforma_mais.integration_port import TransformaMaisIntegrationPort
from transformometro_client import TransformometroApiClient


class TransformometroTransformaMaisGateway(TransformaMaisIntegrationPort):
    def __init__(self, client: TransformometroApiClient | None = None) -> None:
        self._client = client or TransformometroApiClient()

    def list_processes(
        self,
        request: ProcessRequest,
        *,
        authorization: str | None,
    ) -> list[Process]:
        data = self._client.list_engineering_processes(
            params={
                "id": request.id,
                "name_process": request.name_process,
                "filial_id": request.filial_id,
                "sector_name": request.sector_name,
                "status": request.status,
            },
            authorization=authorization,
        )
        items = data.get("items") or []
        return [
            Process(
                id=str(row.get("id") or ""),
                name_process=str(row.get("name_process") or ""),
                filial_id=row.get("filial_id"),
                sector_name=row.get("sector_name"),
                daily_savings=row.get("daily_savings"),
                payback_months=row.get("payback_months"),
                status=row.get("status"),
                implementetion_date=row.get("implementetion_date"),
            )
            for row in items
        ]

    def get_summary(
        self,
        request: ProcessSummaryRequest,
        *,
        authorization: str | None,
    ) -> ProcessSummaryResponse:
        data = self._client.get_engineering_summary(
            params={
                "filial_id": request.filial_id,
                "start_date": request.start_date,
                "end_date": request.end_date,
            },
            authorization=authorization,
        )
        monthly = [
            MonthlySummaryItem(
                month=str(item.get("month") or ""),
                gross_savings_month=float(item.get("gross_savings_month") or 0),
                gross_costs_month=float(item.get("gross_costs_month") or 0),
                gross_investment_month=float(item.get("gross_investment_month") or 0),
                gross_recurring_investment_month=float(
                    item.get("gross_recurring_investment_month") or 0
                ),
                shared_resource_cost_month=float(item.get("shared_resource_cost_month") or 0),
                net_savings_month=float(item.get("net_savings_month") or 0),
            )
            for item in data.get("monthly_breakdown") or []
        ]

        range_raw = data.get("range_summary")
        range_summary = None
        if isinstance(range_raw, dict):
            range_summary = RangeSummary(
                start_date=range_raw.get("start_date"),
                end_date=range_raw.get("end_date"),
                accumulated_net_savings_until_now=float(
                    range_raw.get("accumulated_net_savings_until_now") or 0
                ),
            )

        return ProcessSummaryResponse(
            implemented_solutions_count=int(data.get("implemented_solutions_count") or 0),
            total_net_savings_until_now=float(data.get("total_net_savings_until_now") or 0),
            total_hours_saved_until_now=float(data.get("total_hours_saved_until_now") or 0),
            total_gross_costs_until_now=float(data.get("total_gross_costs_until_now") or 0),
            total_gross_savings_in_period=float(data.get("total_gross_savings_in_period") or 0),
            average_roi=float(data.get("average_roi") or 0),
            monthly_breakdown=monthly,
            range_summary=range_summary,
        )
