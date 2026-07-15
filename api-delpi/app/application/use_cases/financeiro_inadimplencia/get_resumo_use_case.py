from __future__ import annotations

from app.application.dto.financeiro_inadimplencia.query_request import (
    InadimplenciaQueryRequest,
)
from app.application.dto.financeiro_inadimplencia.resumo_response import (
    InadimplenciaResumoResponse,
)
from app.application.use_cases.financeiro_inadimplencia.numeric_helpers import (
    as_float,
    as_int,
    safe_percent,
)
from app.domain.ports.financeiro_inadimplencia.inadimplencia_repository_port import (
    InadimplenciaRepositoryPort,
)


class GetInadimplenciaResumoUseCase:
    def __init__(self, repository: InadimplenciaRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self,
        request: InadimplenciaQueryRequest,
    ) -> InadimplenciaResumoResponse:
        start, end_exclusive, _rotulo = request.resolve_period()
        row = self._repository.get_resumo(
            start_date=start.isoformat(),
            end_date_exclusive=end_exclusive.isoformat(),
        )

        titulos = as_int(row.get("titulos"))
        titulos_em_dia = as_int(row.get("titulos_em_dia"))
        titulos_atraso = as_int(row.get("titulos_atraso"))
        valor_total = as_float(row.get("valor_total"))
        valor_em_dia = as_float(row.get("valor_em_dia"))
        valor_atraso = as_float(row.get("valor_atraso"))

        return InadimplenciaResumoResponse(
            periodo=request.periodo_dict(),
            totais={
                "titulos": titulos,
                "titulos_em_dia": titulos_em_dia,
                "titulos_atraso": titulos_atraso,
                "valor_total": valor_total,
                "valor_atraso": valor_atraso,
            },
            indicadores={
                "percentual_em_dia_qtd": safe_percent(titulos_em_dia, titulos),
                "percentual_inadimplencia_qtd": safe_percent(titulos_atraso, titulos),
                "percentual_em_dia_valor": safe_percent(valor_em_dia, valor_total),
                "percentual_inadimplencia_valor": safe_percent(
                    valor_atraso,
                    valor_total,
                ),
            },
        )
