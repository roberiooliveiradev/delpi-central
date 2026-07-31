"""Mapper row → item de horas improdutivas (EN canônico + aliases camelCase PT)."""

from __future__ import annotations

from typing import Any

from app.application.dto.production.unproductive_hours_request import (
    as_int,
    clean_text,
    display_operator_name,
    iso_date,
    round_cost,
    round_hours,
)
from app.domain.production.unproductive_hours_view_scope import (
    RANK_BY_COST_CENTER,
    RANK_BY_OPERATION,
    RANK_BY_OPERATOR,
    RANK_BY_PRODUCT,
    RANK_BY_RESOURCE,
    RANK_BY_STOP_REASON,
)


class UnproductiveHoursItemMapper:
    @staticmethod
    def map_item(row: dict[str, Any]) -> dict[str, Any]:
        reference_date = iso_date(row.get("data_referencia"))
        branch = clean_text(row.get("filial"))
        production_order = clean_text(row.get("op"))
        product_code = clean_text(row.get("produto"))
        operation = clean_text(row.get("operacao"))
        resource = clean_text(row.get("recurso"))
        cost_center = clean_text(row.get("centro_custo"))
        operator_code = clean_text(row.get("codigo_operador"))
        operator_name = display_operator_name(row.get("nome_operador"))
        stop_reason = clean_text(row.get("motivo"))
        stop_reason_description = clean_text(row.get("motivo_descricao")) or None
        observation = clean_text(row.get("observacao"))
        hours = round_hours(row.get("tempo_horas"))
        stop_cost = round_cost(row.get("valor_parada"))
        cost_source = clean_text(row.get("fonte_custo"))
        return {
            # EN canônico
            "reference_date": reference_date,
            "branch": branch,
            "production_order": production_order,
            "product_code": product_code,
            "operation": operation,
            "resource": resource,
            "cost_center": cost_center,
            "operator_code": operator_code,
            "operator_name": operator_name,
            "stop_reason": stop_reason,
            "stop_reason_description": stop_reason_description,
            "observation": observation,
            "hours": hours,
            "stop_cost": stop_cost,
            "cost_source": cost_source,
            "recno": row.get("recno"),
            # Aliases camelCase PT (legado)
            "dataReferencia": reference_date,
            "filial": branch,
            "op": production_order,
            "produto": product_code,
            "operacao": operation,
            "recurso": resource,
            "centroCusto": cost_center,
            "codigoOperador": operator_code,
            "nomeOperador": operator_name,
            "motivo": stop_reason,
            "motivoDescricao": stop_reason_description,
            "observacao": observation,
            "tempoHoras": hours,
            "valorParada": stop_cost,
            "fonteCusto": cost_source,
        }

    @classmethod
    def map_items(cls, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [cls.map_item(row) for row in rows]

    @staticmethod
    def map_ranking_dimension(rank_by: str, row: dict[str, Any]) -> dict[str, Any]:
        if rank_by == RANK_BY_STOP_REASON:
            reason = clean_text(row.get("motivo"))
            description = clean_text(row.get("motivo_descricao")) or None
            return {
                "stop_reason": reason,
                "stop_reason_description": description,
                "motivo": reason,
                "motivoDescricao": description,
            }
        if rank_by == RANK_BY_RESOURCE:
            resource = clean_text(row.get("recurso"))
            cost_center = clean_text(row.get("centro_custo"))
            return {
                "resource": resource,
                "cost_center": cost_center,
                "recurso": resource,
                "centroCusto": cost_center,
            }
        if rank_by == RANK_BY_COST_CENTER:
            cost_center = clean_text(row.get("centro_custo"))
            return {"cost_center": cost_center, "centroCusto": cost_center}
        if rank_by == RANK_BY_OPERATOR:
            operator_code = clean_text(row.get("codigo_operador"))
            operator_name = display_operator_name(row.get("nome_operador"))
            return {
                "operator_code": operator_code,
                "operator_name": operator_name,
                "codigoOperador": operator_code,
                "nomeOperador": operator_name,
            }
        if rank_by == RANK_BY_PRODUCT:
            product_code = clean_text(row.get("produto"))
            return {"product_code": product_code, "produto": product_code}
        if rank_by == RANK_BY_OPERATION:
            operation = clean_text(row.get("operacao"))
            return {"operation": operation, "operacao": operation}
        return {}

    @classmethod
    def map_ranking_item(
        cls, *, rank: int, rank_by: str, row: dict[str, Any]
    ) -> dict[str, Any]:
        total_appointments = as_int(row.get("total_apontamentos"))
        total_hours = round_hours(row.get("total_horas"))
        total_cost = round_cost(row.get("total_custo"))
        hours_without_cost = round_hours(row.get("horas_sem_custo"))
        return {
            "rank": rank,
            **cls.map_ranking_dimension(rank_by, row),
            "total_appointments": total_appointments,
            "total_hours": total_hours,
            "total_cost": total_cost,
            "hours_without_cost": hours_without_cost,
            "totalApontamentos": total_appointments,
            "totalHoras": total_hours,
            "totalCusto": total_cost,
            "horasSemCusto": hours_without_cost,
        }
