from __future__ import annotations

from app.application.dto.refugos.refugos_formatters import (
    clean_text,
    display_label,
    format_protheus_date,
    round_cost,
    round_qty,
)
from app.application.dto.refugos.refugos_registros_request import RefugosRegistrosRequest
from app.domain.ports.refugos.refugos_repository_port import RefugosRepositoryPort
from app.domain.quality.refugos.refugos_scope import (
    MOTIVO_SEM_LABEL,
    OPERADOR_SEM_NOME_LABEL,
)
from app.infrastructure.persistence.totvs.refugos.refugos_repository import calc_total_pages


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

        items = [
            {
                "filial": clean_text(row.get("filial")),
                "dataPerda": format_protheus_date(row.get("loss_date")),
                "op": clean_text(row.get("production_order")),
                "pa": clean_text(row.get("finished_product")),
                "paDescricao": clean_text(row.get("finished_product_desc")),
                "mp": clean_text(row.get("material_code")),
                "descricao": clean_text(row.get("description")),
                "um": clean_text(row.get("unit")),
                "motivoCodigo": clean_text(row.get("reason_code")),
                "motivo": display_label(
                    row.get("reason_label"), fallback=MOTIVO_SEM_LABEL
                )
                or clean_text(row.get("reason_code")),
                "quantidade": round_qty(row.get("quantity")),
                "valor": round_cost(row.get("value")),
                "custoUnitario": round_cost(row.get("unit_cost")),
                "centroTrabalho": clean_text(row.get("work_center")),
                "codigoOperador": clean_text(row.get("operator_id")),
                "nomeOperador": display_label(
                    row.get("operator_name"), fallback=OPERADOR_SEM_NOME_LABEL
                ),
            }
            for row in rows
        ]

        return {
            "periodo": request.periodo_dict(),
            "items": items,
            "page": page,
            "pageSize": page_size,
            "total": total,
            "totalPages": calc_total_pages(total, page_size),
            "summary": {
                "branch": request.query.period.filial,
                "branch_filter_applied": True,
                "period": {
                    "start": request.query.period.start_date.isoformat(),
                    "end": request.query.period.end_date.isoformat(),
                },
                "is_complete": True,
            },
        }
