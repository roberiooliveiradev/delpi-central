from __future__ import annotations

from app.application.dto.financeiro_inadimplencia.constantes import FAIXAS_ATRASO
from app.application.dto.financeiro_inadimplencia.faixas_atraso_response import (
    InadimplenciaFaixaAtrasoItem,
    InadimplenciaFaixasAtrasoResponse,
)
from app.application.dto.financeiro_inadimplencia.query_request import (
    InadimplenciaQueryRequest,
)
from app.application.use_cases.financeiro_inadimplencia.numeric_helpers import (
    as_float,
    as_int,
    as_str,
    safe_percent,
)
from app.domain.ports.financeiro_inadimplencia.inadimplencia_repository_port import (
    InadimplenciaRepositoryPort,
)


class GetInadimplenciaFaixasAtrasoUseCase:
    def __init__(self, repository: InadimplenciaRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self,
        request: InadimplenciaQueryRequest,
    ) -> InadimplenciaFaixasAtrasoResponse:
        start, end_exclusive, _rotulo = request.resolve_period()
        rows = self._repository.get_faixas_atraso(
            start_date=start.isoformat(),
            end_date_exclusive=end_exclusive.isoformat(),
        )

        by_code: dict[str, dict] = {
            as_str(row.get("codigo")): row for row in rows if as_str(row.get("codigo"))
        }

        total_quantidade = sum(as_int(row.get("quantidade")) for row in rows)
        total_valor = sum(as_float(row.get("valor")) for row in rows)

        items: list[InadimplenciaFaixaAtrasoItem] = []
        for faixa in FAIXAS_ATRASO:
            row = by_code.get(faixa.codigo, {})
            quantidade = as_int(row.get("quantidade"))
            valor = as_float(row.get("valor"))
            items.append(
                InadimplenciaFaixaAtrasoItem(
                    codigo=faixa.codigo,
                    rotulo=faixa.rotulo,
                    ordem=faixa.ordem,
                    quantidade=quantidade,
                    valor=valor,
                    percentual_quantidade=safe_percent(quantidade, total_quantidade),
                    percentual_valor=safe_percent(valor, total_valor),
                )
            )

        return InadimplenciaFaixasAtrasoResponse(
            periodo=request.periodo_dict(),
            items=items,
        )
