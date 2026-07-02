from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DespesasCentroCustoLancamentoItem:
    filial: str
    data_emissao: str
    data_emissao_formatada: str
    centro_custo_codigo: str
    centro_custo_descricao: str
    fornecedor_cliente_codigo: str
    loja: str
    razao_social: str
    documento: str
    serie: str
    pedido: str
    item: str
    item_pedido: str
    produto_codigo: str
    produto_descricao: str
    observacoes: str
    quantidade: float
    valor_unitario: float
    valor_total: float
    conta_contabil: str
    rateio: str
    tes: str
    cfop: str
    tipo_documento: str
    tipo_produto_lancamento: str
    recno_sd1: int

    def to_dict(self) -> dict:
        return {
            "filial": self.filial,
            "data_emissao": self.data_emissao,
            "data_emissao_formatada": self.data_emissao_formatada,
            "centro_custo_codigo": self.centro_custo_codigo,
            "centro_custo_descricao": self.centro_custo_descricao,
            "fornecedor_cliente_codigo": self.fornecedor_cliente_codigo,
            "loja": self.loja,
            "razao_social": self.razao_social,
            "documento": self.documento,
            "serie": self.serie,
            "pedido": self.pedido,
            "item": self.item,
            "item_pedido": self.item_pedido,
            "produto_codigo": self.produto_codigo,
            "produto_descricao": self.produto_descricao,
            "observacoes": self.observacoes,
            "quantidade": self.quantidade,
            "valor_unitario": self.valor_unitario,
            "valor_total": self.valor_total,
            "conta_contabil": self.conta_contabil,
            "rateio": self.rateio,
            "tes": self.tes,
            "cfop": self.cfop,
            "tipo_documento": self.tipo_documento,
            "tipo_produto_lancamento": self.tipo_produto_lancamento,
            "recno_sd1": self.recno_sd1,
        }


@dataclass
class DespesasCentroCustoLancamentosPagination:
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool

    def to_dict(self) -> dict:
        return {
            "page": self.page,
            "page_size": self.page_size,
            "total_items": self.total_items,
            "total_pages": self.total_pages,
            "has_next": self.has_next,
            "has_previous": self.has_previous,
        }


@dataclass
class DespesasCentroCustoLancamentosResponse:
    periodo: dict[str, str]
    pagination: DespesasCentroCustoLancamentosPagination
    sort: dict[str, str]
    items: list[DespesasCentroCustoLancamentoItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "periodo": self.periodo,
            "pagination": self.pagination.to_dict(),
            "sort": self.sort,
            "items": [item.to_dict() for item in self.items],
        }
