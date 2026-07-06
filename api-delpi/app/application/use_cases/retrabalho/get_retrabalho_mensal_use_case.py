from __future__ import annotations

from app.application.dto.retrabalho.retrabalho_formatters import as_int, round_cost, round_hours
from app.application.dto.retrabalho.retrabalho_query_request import RetrabalhoQueryRequest
from app.domain.ports.retrabalho.retrabalho_repository_port import RetrabalhoRepositoryPort


class GetRetrabalhoMensalUseCase:
    def __init__(self, repository: RetrabalhoRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: RetrabalhoQueryRequest) -> dict:
        start_date, end_date = request.period.iso_range()
        rows = self._repository.get_mensal(
            start_date=start_date,
            end_date=end_date,
            branch=request.period.filial,
            recurso=request.recurso,
            centro_custo=request.centro_custo,
            codigo_operador=request.codigo_operador,
        )

        items = [
            {
                "anoMes": row.get("ano_mes") or "",
                "ano": as_int(row.get("ANO") or row.get("ano")),
                "mesNumero": as_int(row.get("MES_NUMERO") or row.get("mes_numero")),
                "mesNome": row.get("mes_nome") or "",
                "totalApontamentos": as_int(row.get("total_apontamentos")),
                "totalHoras": round_hours(row.get("total_horas")),
                "totalCusto": round_cost(row.get("total_custo")),
                "horasSemCusto": round_hours(row.get("horas_sem_custo")),
            }
            for row in rows
        ]

        return {
            "periodo": request.periodo_dict(),
            "items": items,
        }
