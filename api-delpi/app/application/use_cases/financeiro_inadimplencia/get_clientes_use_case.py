from __future__ import annotations

from app.application.dto.financeiro_inadimplencia.clientes_request import (
    InadimplenciaClientesRequest,
)
from app.application.dto.financeiro_inadimplencia.clientes_response import (
    InadimplenciaClienteItem,
    InadimplenciaClientesResponse,
    InadimplenciaPagination,
)
from app.application.use_cases.financeiro_inadimplencia.numeric_helpers import (
    as_float,
    as_int,
    as_str,
    build_pagination,
)
from app.domain.ports.financeiro_inadimplencia.inadimplencia_repository_port import (
    InadimplenciaRepositoryPort,
)


class GetInadimplenciaClientesUseCase:
    def __init__(self, repository: InadimplenciaRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self,
        request: InadimplenciaClientesRequest,
    ) -> InadimplenciaClientesResponse:
        start, end_exclusive, _rotulo = request.resolve_period()
        page = request.resolve_page()
        page_size = request.resolve_page_size()
        start_iso = start.isoformat()
        end_iso = end_exclusive.isoformat()

        total_items = self._repository.count_clientes(
            start_date=start_iso,
            end_date_exclusive=end_iso,
            q=request.q,
            only_with_delays=request.only_with_delays,
        )
        rows = self._repository.list_clientes(
            start_date=start_iso,
            end_date_exclusive=end_iso,
            q=request.q,
            only_with_delays=request.only_with_delays,
            sort_by=request.sort_by,
            sort_dir=request.sort_dir,
            page=page,
            page_size=page_size,
        )

        pagination = build_pagination(
            page=page,
            page_size=page_size,
            total_items=total_items,
        )

        return InadimplenciaClientesResponse(
            periodo=request.periodo_dict(),
            pagination=InadimplenciaPagination(**pagination),
            sort={"sort_by": request.sort_by, "sort_dir": request.sort_dir},
            items=[
                InadimplenciaClienteItem(
                    cliente_codigo=as_str(row.get("cliente_codigo")),
                    loja=as_str(row.get("loja")),
                    nome_cliente=as_str(row.get("nome_cliente")),
                    nome_reduzido=as_str(row.get("nome_reduzido")),
                    total_titulos=as_int(row.get("total_titulos")),
                    titulos_em_dia=as_int(row.get("titulos_em_dia")),
                    titulos_atraso=as_int(row.get("titulos_atraso")),
                    valor_total=as_float(row.get("valor_total")),
                    valor_atraso=as_float(row.get("valor_atraso")),
                    percentual_em_dia_qtd=as_float(row.get("percentual_em_dia_qtd")),
                    percentual_em_dia_valor=as_float(
                        row.get("percentual_em_dia_valor")
                    ),
                )
                for row in rows
            ],
        )
