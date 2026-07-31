from __future__ import annotations

from typing import Any

from app.application.dto.refugos.refugos_formatters import (
    clean_text,
    display_label,
    format_code_dash_label,
    format_protheus_date,
    round_cost,
    round_qty,
)
from app.application.dto.refugos.refugos_registros_request import RefugosRegistrosRequest
from app.application.services.paged_list_envelope_service import build_paged_list_envelope
from app.domain.ports.refugos.refugos_repository_port import RefugosRepositoryPort
from app.domain.quality.refugos.refugos_scope import (
    MOTIVO_SEM_LABEL,
    OPERADOR_SEM_NOME_LABEL,
)


def _map_registro_item(row: dict[str, Any]) -> dict[str, Any]:
    branch = clean_text(row.get("filial"))
    loss_date = format_protheus_date(row.get("loss_date"))
    production_order = clean_text(row.get("production_order"))
    finished_product = clean_text(row.get("finished_product"))
    finished_product_description = clean_text(row.get("finished_product_desc"))
    material_code = clean_text(row.get("material_code"))
    description = clean_text(row.get("description"))
    unit = clean_text(row.get("unit"))
    reason_code = clean_text(row.get("reason_code"))
    reason = format_code_dash_label(
        row.get("reason_code"),
        row.get("reason_label"),
        empty_fallback=MOTIVO_SEM_LABEL,
    )
    quantity = round_qty(row.get("quantity"))
    value = round_cost(row.get("value"))
    unit_cost = round_cost(row.get("unit_cost"))
    work_center = clean_text(row.get("work_center"))
    operator_code = clean_text(row.get("operator_id"))
    operator_name = display_label(
        row.get("operator_name"), fallback=OPERADOR_SEM_NOME_LABEL
    )
    return {
        # EN canônico (aditivo)
        "branch": branch,
        "loss_date": loss_date,
        "production_order": production_order,
        "finished_product": finished_product,
        "finished_product_description": finished_product_description,
        "material_code": material_code,
        "description": description,
        "unit": unit,
        "reason_code": reason_code,
        "reason": reason,
        "quantity": quantity,
        "value": value,
        "unit_cost": unit_cost,
        "work_center": work_center,
        "operator_code": operator_code,
        "operator_name": operator_name,
        # camelCase PT (legado MFE)
        "filial": branch,
        "dataPerda": loss_date,
        "op": production_order,
        "pa": finished_product,
        "paDescricao": finished_product_description,
        "mp": material_code,
        "descricao": description,
        "um": unit,
        "motivoCodigo": reason_code,
        "motivo": reason,
        "quantidade": quantity,
        "valor": value,
        "custoUnitario": unit_cost,
        "centroTrabalho": work_center,
        "codigoOperador": operator_code,
        "nomeOperador": operator_name,
    }


class GetRefugosRegistrosUseCase:
    def __init__(self, repository: RefugosRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: RefugosRegistrosRequest) -> dict:
        date_start, date_end_exclusive = request.query.period.protheus_closed_open()
        page = request.resolve_page()
        page_size = request.resolve_page_size()
        offset = (page - 1) * page_size
        filters = request.query.filter_kwargs()

        total = self._repository.count_registros(
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
            branch=request.query.period.filial,
            **filters,
        )
        rows = self._repository.get_registros(
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
            branch=request.query.period.filial,
            offset=offset,
            page_size=page_size,
            **filters,
        )

        return build_paged_list_envelope(
            page=page,
            page_size=page_size,
            total=total,
            items=[_map_registro_item(row) for row in rows],
            extra={
                "periodo": request.periodo_dict(),
                "summary": {
                    "branch": request.query.period.filial,
                    "branch_filter_applied": True,
                    "period": {
                        "start": request.query.period.start_date.isoformat(),
                        "end": request.query.period.end_date.isoformat(),
                    },
                    "is_complete": True,
                },
            },
        )
