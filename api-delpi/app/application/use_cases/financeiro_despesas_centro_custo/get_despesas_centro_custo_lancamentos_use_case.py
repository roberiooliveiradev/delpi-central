from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.application.dto.financeiro_despesas_centro_custo.despesas_centro_custo_lancamentos_request import (
    DespesasCentroCustoLancamentosRequest,
)
from app.application.dto.financeiro_despesas_centro_custo.despesas_centro_custo_lancamentos_response import (
    DespesasCentroCustoLancamentoItem,
    DespesasCentroCustoLancamentosPagination,
    DespesasCentroCustoLancamentosResponse,
)
from app.application.services.response_date_format_service import (
    ResponseDateFormatService,
)
from app.domain.ports.financeiro_despesas_centro_custo.despesas_centro_custo_repository_port import (
    DespesasCentroCustoRepositoryPort,
)


def _as_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _as_int(value: Any) -> int:
    if value is None or value == "":
        return 0
    if isinstance(value, (int, float, Decimal)):
        return int(value)
    text = str(value).strip().replace(",", ".")
    return int(float(text))


def _as_float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    if isinstance(value, (int, float, Decimal)):
        return round(float(value), 4 if isinstance(value, Decimal) else 2)
    text = str(value).strip().replace(",", ".")
    return round(float(text), 2)


def _normalize_item(row: dict) -> DespesasCentroCustoLancamentoItem:
    raw_emissao = _as_str(row.get("data_emissao"))
    data_emissao_iso = ResponseDateFormatService.format_date(raw_emissao) or raw_emissao
    return DespesasCentroCustoLancamentoItem(
        filial=_as_str(row.get("filial")),
        data_emissao=data_emissao_iso,
        data_emissao_formatada=_as_str(row.get("data_emissao_formatada")),
        centro_custo_codigo=_as_str(row.get("centro_custo_codigo")),
        centro_custo_descricao=_as_str(row.get("centro_custo_descricao")),
        fornecedor_cliente_codigo=_as_str(row.get("fornecedor_cliente_codigo")),
        loja=_as_str(row.get("loja")),
        razao_social=_as_str(row.get("razao_social")),
        documento=_as_str(row.get("documento")),
        serie=_as_str(row.get("serie")),
        pedido=_as_str(row.get("pedido")),
        item=_as_str(row.get("item")),
        item_pedido=_as_str(row.get("item_pedido")),
        produto_codigo=_as_str(row.get("produto_codigo")),
        produto_descricao=_as_str(row.get("produto_descricao")),
        observacoes=_as_str(row.get("observacoes")),
        quantidade=_as_float(row.get("quantidade")),
        valor_unitario=_as_float(row.get("valor_unitario")),
        valor_total=_as_float(row.get("valor_total")),
        conta_contabil=_as_str(row.get("conta_contabil")),
        rateio=_as_str(row.get("rateio")),
        tes=_as_str(row.get("tes")),
        cfop=_as_str(row.get("cfop")),
        tipo_documento=_as_str(row.get("tipo_documento")),
        tipo_produto_lancamento=_as_str(row.get("tipo_produto_lancamento")),
        recno_sd1=_as_int(row.get("recno_sd1")),
    )


class GetDespesasCentroCustoLancamentosUseCase:
    def __init__(self, repository: DespesasCentroCustoRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self,
        request: DespesasCentroCustoLancamentosRequest,
    ) -> DespesasCentroCustoLancamentosResponse:
        start_date, end_date = request.resolve_protheus_period()
        page = request.resolve_page()
        page_size = request.resolve_page_size()
        search = str(request.search or "").strip() or None

        scope = dict(
            start_date=start_date,
            end_date=end_date,
            branch=request.branch,
            cost_center=request.cost_center,
            supplier_code=request.supplier_code,
            supplier_store=request.supplier_store,
            exclude_mp_products=request.exclude_mp_products,
        )

        # COUNT(*) na view chega a ~15s no mês; o /resumo (cacheado) já traz
        # quantidade_lancamentos no mesmo filtro. Com busca textual, usa overfetch
        # (page_size+1) e evita o COUNT pesado.
        if search:
            fetch_size = page_size + 1
            rows = self._repository.list_lancamentos(
                **scope,
                search=search,
                sort_by=request.sort_by,
                sort_dir=request.sort_dir,
                page=page,
                page_size=fetch_size,
            )
            has_next = len(rows) > page_size
            rows = rows[:page_size]
            total_items = (page - 1) * page_size + len(rows) + (1 if has_next else 0)
            total_pages = page + (1 if has_next else 0)
            if page > 1 and not rows and not has_next:
                total_pages = max(page - 1, 1)
                total_items = (page - 1) * page_size
        else:
            resumo = self._repository.get_resumo(**scope)
            total_items = _as_int(resumo.get("quantidade_lancamentos"))
            rows = self._repository.list_lancamentos(
                **scope,
                search=None,
                sort_by=request.sort_by,
                sort_dir=request.sort_dir,
                page=page,
                page_size=page_size,
            )
            total_pages = (
                max((total_items + page_size - 1) // page_size, 1) if total_items else 1
            )
            has_next = page < total_pages

        return DespesasCentroCustoLancamentosResponse(
            periodo=request.periodo_dict(),
            pagination=DespesasCentroCustoLancamentosPagination(
                page=page,
                page_size=page_size,
                total_items=total_items,
                total=total_items,
                total_pages=total_pages,
                has_next=has_next,
                has_previous=page > 1,
                is_complete=not has_next,
            ),
            sort={
                "sort_by": request.sort_by,
                "sort_dir": request.sort_dir,
            },
            items=[_normalize_item(row) for row in rows],
        )
