"""Assembler — respostas de horas improdutivas."""

from __future__ import annotations

from typing import Any

from app.application.dto.production.unproductive_hours_request import (
    UnproductiveHoursItemsRequest,
    UnproductiveHoursQueryRequest,
    UnproductiveHoursRankingRequest,
    as_int,
    display_operator_name,
    round_cost,
    round_hours,
)
from app.application.services.paged_list_envelope_service import build_paged_list_envelope
from app.domain.services.production.unproductive_hours_item_mapper import (
    UnproductiveHoursItemMapper,
)


class UnproductiveHoursResponseAssembler:
    @staticmethod
    def to_summary(
        *,
        request: UnproductiveHoursQueryRequest,
        row: dict[str, Any],
        top_resource: dict[str, Any] | None,
        top_operator: dict[str, Any] | None,
    ) -> dict[str, Any]:
        total_appointments = as_int(row.get("total_apontamentos"))
        total_hours = round_hours(row.get("total_horas"))
        total_cost = round_cost(row.get("total_custo"))
        records_without_cost = as_int(row.get("registros_sem_custo"))
        hours_without_cost = round_hours(row.get("horas_sem_custo"))
        pct_hours_without_cost = (
            round((hours_without_cost / total_hours) * 100, 2) if total_hours > 0 else 0.0
        )
        avg_cost_per_hour = (
            round(total_cost / total_hours, 2) if total_hours > 0 else 0.0
        )

        top_resource_payload = None
        if top_resource and top_resource.get("recurso"):
            hours = round_hours(top_resource.get("total_horas"))
            resource = top_resource.get("recurso") or ""
            top_resource_payload = {
                "resource": resource,
                "total_hours": hours,
                "recurso": resource,
                "totalHoras": hours,
            }

        top_operator_payload = None
        if top_operator and top_operator.get("codigo_operador"):
            hours = round_hours(top_operator.get("total_horas"))
            operator_code = top_operator.get("codigo_operador") or ""
            operator_name = display_operator_name(top_operator.get("nome_operador"))
            top_operator_payload = {
                "operator_code": operator_code,
                "operator_name": operator_name,
                "total_hours": hours,
                "codigoOperador": operator_code,
                "nomeOperador": operator_name,
                "totalHoras": hours,
            }

        summary = {
            "total_appointments": total_appointments,
            "total_hours": total_hours,
            "total_cost": total_cost,
            "avg_cost_per_hour": avg_cost_per_hour,
            "records_without_cost": records_without_cost,
            "hours_without_cost": hours_without_cost,
            "pct_hours_without_cost": pct_hours_without_cost,
            "top_resource_by_hours": top_resource_payload,
            "top_operator_by_hours": top_operator_payload,
            # Aliases camelCase PT
            "totalApontamentos": total_appointments,
            "totalHoras": total_hours,
            "totalCusto": total_cost,
            "custoMedioHora": avg_cost_per_hour,
            "registrosSemCusto": records_without_cost,
            "horasSemCusto": hours_without_cost,
            "percentualHorasSemCusto": pct_hours_without_cost,
            "principalRecursoPorHoras": top_resource_payload,
            "principalColaboradorPorHoras": top_operator_payload,
        }
        return {"periodo": request.periodo_dict(), "summary": summary}

    @staticmethod
    def to_items(
        *,
        request: UnproductiveHoursItemsRequest,
        total: int,
        rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        items = UnproductiveHoursItemMapper.map_items(rows)
        return build_paged_list_envelope(
            page=request.page,
            page_size=request.page_size,
            total=total,
            items=items,
            extra={"periodo": request.periodo_dict(), "sort": request.sort},
        )

    @staticmethod
    def to_ranking(
        *,
        request: UnproductiveHoursRankingRequest,
        rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        items = [
            UnproductiveHoursItemMapper.map_ranking_item(
                rank=index, rank_by=request.rank_by, row=row
            )
            for index, row in enumerate(rows, start=1)
        ]
        return {
            "periodo": request.periodo_dict(),
            "rank_by": request.rank_by,
            "rankBy": request.rank_by,
            "metric": request.metric,
            "limit": request.limit,
            "items": items,
        }
