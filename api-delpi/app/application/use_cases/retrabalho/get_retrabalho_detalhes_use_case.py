from __future__ import annotations

from typing import Any

from app.application.dto.retrabalho.retrabalho_detalhes_request import RetrabalhoDetalhesRequest
from app.application.dto.retrabalho.retrabalho_formatters import (
    display_operador_nome,
    round_cost,
    round_hours,
)
from app.application.services.paged_list_envelope_service import build_paged_list_envelope
from app.domain.ports.retrabalho.retrabalho_repository_port import RetrabalhoRepositoryPort


def _map_detalhe_item(row: dict[str, Any]) -> dict[str, Any]:
    reference_date = row.get("DATA_REFERENCIA") or row.get("data_referencia") or ""
    branch = row.get("filial") or ""
    production_order = row.get("op") or ""
    product_code = row.get("produto") or ""
    operation = row.get("operacao") or ""
    resource = row.get("recurso") or ""
    cost_center = row.get("centro_custo") or ""
    operator_code = row.get("codigo_operador") or ""
    operator_name = display_operador_nome(row.get("nome_operador"))
    hours = round_hours(row.get("tempo_horas"))
    stop_cost = round_cost(row.get("valor_parada"))
    cost_source = row.get("fonte_custo") or ""
    stop_reason = row.get("motivo") or ""
    observation = row.get("observacao") or ""
    recno = int(row.get("RECNO") or row.get("recno") or 0)
    return {
        # EN canônico (aditivo)
        "reference_date": reference_date,
        "branch": branch,
        "production_order": production_order,
        "product_code": product_code,
        "operation": operation,
        "resource": resource,
        "cost_center": cost_center,
        "operator_code": operator_code,
        "operator_name": operator_name,
        "hours": hours,
        "stop_cost": stop_cost,
        "cost_source": cost_source,
        "stop_reason": stop_reason,
        "observation": observation,
        "recno": recno,
        # camelCase PT (legado MFE)
        "dataReferencia": reference_date,
        "filial": branch,
        "op": production_order,
        "produto": product_code,
        "operacao": operation,
        "recurso": resource,
        "centroCusto": cost_center,
        "codigoOperador": operator_code,
        "nomeOperador": operator_name,
        "tempoHoras": hours,
        "valorParada": stop_cost,
        "fonteCusto": cost_source,
        "motivo": stop_reason,
        "observacao": observation,
    }


class GetRetrabalhoDetalhesUseCase:
    def __init__(self, repository: RetrabalhoRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: RetrabalhoDetalhesRequest) -> dict:
        start_date, end_date = request.query.period.iso_range()
        page = request.resolve_page()
        page_size = request.resolve_page_size()
        offset = (page - 1) * page_size

        common = {
            "start_date": start_date,
            "end_date": end_date,
            "branch": request.query.period.filial,
            "recurso": request.query.recurso,
            "centro_custo": request.query.centro_custo,
            "codigo_operador": request.query.codigo_operador,
        }

        total = self._repository.count_detalhes(**common)
        rows = self._repository.get_detalhes(
            **common,
            sort_by=request.sort_by,
            sort_dir=request.sort_dir,
            offset=offset,
            page_size=page_size,
        )

        return build_paged_list_envelope(
            page=page,
            page_size=page_size,
            total=total,
            items=[_map_detalhe_item(row) for row in rows],
            extra={
                "periodo": request.periodo_dict(),
                "orderBy": request.sort_by,
                "orderDir": request.sort_dir,
            },
        )
