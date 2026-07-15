from __future__ import annotations

from app.application.dto.refugos.refugos_formatters import as_int, round_cost, round_qty
from app.application.dto.refugos.refugos_query_request import RefugosQueryRequest
from app.domain.ports.refugos.refugos_repository_port import RefugosRepositoryPort


class GetRefugosResumoUseCase:
    def __init__(self, repository: RefugosRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: RefugosQueryRequest) -> dict:
        date_start, date_end_exclusive = request.period.protheus_closed_open()
        day_start, day_end_exclusive = request.period.day_closed_open()
        month_start, month_end_exclusive = request.period.month_closed_open()

        row = self._repository.get_resumo(
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
            branch=request.period.filial,
            day_start=day_start,
            day_end_exclusive=day_end_exclusive,
            month_start=month_start,
            month_end_exclusive=month_end_exclusive,
            **request.filter_kwargs(),
        )

        return {
            "periodo": request.periodo_dict(),
            "totalValor": round_cost(row.get("total_valor")),
            "totalQuantidade": round_qty(row.get("total_quantidade")),
            "ocorrencias": as_int(row.get("ocorrencias")),
            "registrosSemCusto": as_int(row.get("registros_sem_custo")),
            "valorDia": round_cost(row.get("valor_dia")),
            "valorMes": round_cost(row.get("valor_mes")),
            "branchFilterApplied": True,
            "summary": {
                "branch": request.period.filial,
                "branch_filter_applied": True,
                "period": {
                    "start": request.period.start_date.isoformat(),
                    "end": request.period.end_date.isoformat(),
                },
                "is_complete": True,
            },
        }
