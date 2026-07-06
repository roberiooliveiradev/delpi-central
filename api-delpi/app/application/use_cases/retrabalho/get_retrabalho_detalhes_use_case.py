from __future__ import annotations

from app.application.dto.retrabalho.retrabalho_detalhes_request import RetrabalhoDetalhesRequest
from app.application.dto.retrabalho.retrabalho_formatters import (
    display_operador_nome,
    round_cost,
    round_hours,
)
from app.domain.ports.retrabalho.retrabalho_repository_port import RetrabalhoRepositoryPort
from app.infrastructure.persistence.totvs.retrabalho.retrabalho_repository import calc_total_pages


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

        items = [
            {
                "dataReferencia": row.get("DATA_REFERENCIA") or row.get("data_referencia") or "",
                "filial": row.get("filial") or "",
                "op": row.get("op") or "",
                "produto": row.get("produto") or "",
                "operacao": row.get("operacao") or "",
                "recurso": row.get("recurso") or "",
                "centroCusto": row.get("centro_custo") or "",
                "codigoOperador": row.get("codigo_operador") or "",
                "nomeOperador": display_operador_nome(row.get("nome_operador")),
                "tempoHoras": round_hours(row.get("tempo_horas")),
                "valorParada": round_cost(row.get("valor_parada")),
                "fonteCusto": row.get("fonte_custo") or "",
                "motivo": row.get("motivo") or "",
                "observacao": row.get("observacao") or "",
                "recno": int(row.get("RECNO") or row.get("recno") or 0),
            }
            for row in rows
        ]

        total_pages = calc_total_pages(total, page_size)

        return {
            "periodo": request.periodo_dict(),
            "items": items,
            "page": page,
            "pageSize": page_size,
            "total": total,
            "totalPages": total_pages,
            "orderBy": request.sort_by,
            "orderDir": request.sort_dir,
        }
