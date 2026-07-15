from __future__ import annotations

from app.application.dto.financeiro_inadimplencia.mensal_request import (
    InadimplenciaMensalQueryRequest,
)
from app.application.dto.financeiro_inadimplencia.mensal_response import (
    InadimplenciaMensalItem,
    InadimplenciaMensalResponse,
)
from app.application.use_cases.financeiro_inadimplencia.numeric_helpers import (
    as_float,
    as_int,
    as_iso_date,
    as_str,
    safe_percent,
)
from app.domain.ports.financeiro_inadimplencia.inadimplencia_repository_port import (
    InadimplenciaRepositoryPort,
)


class GetInadimplenciaMensalUseCase:
    def __init__(self, repository: InadimplenciaRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self,
        request: InadimplenciaMensalQueryRequest,
    ) -> InadimplenciaMensalResponse:
        start, end_exclusive, _rotulo = request.resolve_period()
        rows = self._repository.get_mensal(
            start_date=start.isoformat(),
            end_date_exclusive=end_exclusive.isoformat(),
            customer_code=request.customer_code,
            store_code=request.store_code,
            customer_pairs=request.customer_pairs,
            novos_negocios=request.novos_negocios,
        )

        items: list[InadimplenciaMensalItem] = []
        for row in rows:
            mes = as_iso_date(row.get("mes"))
            total_titulos = as_int(row.get("total_titulos"))
            titulos_em_dia = as_int(row.get("titulos_em_dia"))
            titulos_atraso = as_int(row.get("titulos_atraso"))
            valor_total = as_float(row.get("valor_total"))
            valor_em_dia = as_float(row.get("valor_em_dia"))
            valor_atraso = as_float(row.get("valor_atraso"))
            items.append(
                InadimplenciaMensalItem(
                    mes=mes,
                    ano_mes=mes[:7] if len(mes) >= 7 else as_str(row.get("mes")),
                    total_titulos=total_titulos,
                    titulos_em_dia=titulos_em_dia,
                    titulos_atraso=titulos_atraso,
                    valor_total=valor_total,
                    valor_em_dia=valor_em_dia,
                    valor_atraso=valor_atraso,
                    percentual_em_dia_qtd=safe_percent(titulos_em_dia, total_titulos),
                    percentual_em_dia_valor=safe_percent(valor_em_dia, valor_total),
                )
            )

        return InadimplenciaMensalResponse(
            periodo=request.periodo_dict(),
            items=items,
        )
