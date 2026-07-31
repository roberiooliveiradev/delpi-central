"""Use case — itens paginados de horas improdutivas."""

from __future__ import annotations

from app.application.dto.production.unproductive_hours_request import (
    UnproductiveHoursItemsRequest,
    clean_text,
    display_operator_name,
    iso_date,
    round_cost,
    round_hours,
)
from app.domain.ports.production.unproductive_hours_repository_port import (
    UnproductiveHoursRepositoryPort,
)


class GetProductionUnproductiveHoursItemsUseCase:
    def __init__(self, repository: UnproductiveHoursRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: UnproductiveHoursItemsRequest) -> dict:
        common = request.filter_kwargs()
        total = self._repository.count_items(**common)
        rows = self._repository.get_items(
            **common,
            sort=request.sort,
            offset=request.offset,
            page_size=request.page_size,
        )
        total_pages = (
            (total + request.page_size - 1) // request.page_size if total else 0
        )
        items = []
        for row in rows:
            motivo_descricao = clean_text(row.get("motivo_descricao")) or None
            items.append(
                {
                    "dataReferencia": iso_date(row.get("data_referencia")),
                    "filial": clean_text(row.get("filial")),
                    "op": clean_text(row.get("op")),
                    "produto": clean_text(row.get("produto")),
                    "operacao": clean_text(row.get("operacao")),
                    "recurso": clean_text(row.get("recurso")),
                    "centroCusto": clean_text(row.get("centro_custo")),
                    "codigoOperador": clean_text(row.get("codigo_operador")),
                    "nomeOperador": display_operator_name(row.get("nome_operador")),
                    "motivo": clean_text(row.get("motivo")),
                    "motivoDescricao": motivo_descricao,
                    "observacao": clean_text(row.get("observacao")),
                    "tempoHoras": round_hours(row.get("tempo_horas")),
                    "valorParada": round_cost(row.get("valor_parada")),
                    "fonteCusto": clean_text(row.get("fonte_custo")),
                    "recno": row.get("recno"),
                }
            )
        return {
            "periodo": request.periodo_dict(),
            "items": items,
            "page": request.page,
            "pageSize": request.page_size,
            "total": total,
            "totalPages": total_pages,
            "sort": request.sort,
            "pagination": {
                "page": request.page,
                "page_size": request.page_size,
                "total": total,
                "total_pages": total_pages,
                "is_complete": request.page >= total_pages if total_pages else True,
            },
        }
