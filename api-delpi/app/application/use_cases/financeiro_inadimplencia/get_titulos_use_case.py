from __future__ import annotations

from app.application.dto.financeiro_inadimplencia.clientes_response import (
    InadimplenciaPagination,
)
from app.application.dto.financeiro_inadimplencia.constantes import (
    FAIXA_ATRASO_BY_CODE,
)
from app.application.dto.financeiro_inadimplencia.titulos_request import (
    InadimplenciaTitulosRequest,
)
from app.application.dto.financeiro_inadimplencia.titulos_response import (
    InadimplenciaTituloItem,
    InadimplenciaTitulosResponse,
)
from app.application.use_cases.financeiro_inadimplencia.numeric_helpers import (
    as_bool,
    as_float,
    as_int,
    as_iso_date,
    as_str,
    build_pagination,
)
from app.domain.ports.financeiro_inadimplencia.inadimplencia_repository_port import (
    InadimplenciaRepositoryPort,
)


class GetInadimplenciaTitulosUseCase:
    def __init__(self, repository: InadimplenciaRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self,
        request: InadimplenciaTitulosRequest,
    ) -> InadimplenciaTitulosResponse:
        start, end_exclusive, _rotulo = request.resolve_period()
        page = request.resolve_page()
        page_size = request.resolve_page_size()
        start_iso = start.isoformat()
        end_iso = end_exclusive.isoformat()

        total_items = self._repository.count_titulos(
            start_date=start_iso,
            end_date_exclusive=end_iso,
            customer_code=request.customer_code,
            store_code=request.store_code,
            status=request.status,
            delay_range=request.delay_range,
            q=request.q,
        )
        rows = self._repository.list_titulos(
            start_date=start_iso,
            end_date_exclusive=end_iso,
            customer_code=request.customer_code,
            store_code=request.store_code,
            status=request.status,
            delay_range=request.delay_range,
            q=request.q,
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

        return InadimplenciaTitulosResponse(
            periodo=request.periodo_dict(),
            pagination=InadimplenciaPagination(**pagination),
            sort={"sort_by": request.sort_by, "sort_dir": request.sort_dir},
            items=[self._normalize_item(row) for row in rows],
        )

    @staticmethod
    def _normalize_item(row: dict) -> InadimplenciaTituloItem:
        codigo_faixa = as_str(row.get("faixa_atraso"))
        faixa = FAIXA_ATRASO_BY_CODE.get(codigo_faixa)
        return InadimplenciaTituloItem(
            filial=as_str(row.get("filial")),
            prefixo=as_str(row.get("prefixo")),
            numero=as_str(row.get("numero")),
            parcela=as_str(row.get("parcela")),
            tipo=as_str(row.get("tipo")),
            cliente_codigo=as_str(row.get("cliente_codigo")),
            loja=as_str(row.get("loja")),
            nome_cliente=as_str(row.get("nome_cliente")),
            nome_reduzido=as_str(row.get("nome_reduzido")),
            data_emissao=as_iso_date(row.get("data_emissao")),
            data_vencimento_real=as_iso_date(row.get("data_vencimento_real")),
            data_baixa=as_iso_date(row.get("data_baixa")),
            valor_titulo=as_float(row.get("valor_titulo")),
            pago_em_dia=as_bool(row.get("pago_em_dia")),
            dias_atraso=as_int(row.get("dias_atraso")),
            faixa_atraso={
                "codigo": codigo_faixa,
                "rotulo": faixa.rotulo if faixa else codigo_faixa,
            },
        )
