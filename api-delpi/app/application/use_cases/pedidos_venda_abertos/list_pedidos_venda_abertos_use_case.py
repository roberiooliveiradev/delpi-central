from __future__ import annotations

from typing import Any

from app.application.dto.pedidos_venda_abertos.list_pedidos_venda_abertos_response import (
    ListPedidosVendaAbertosResponse,
    PedidosVendaAbertosSummary,
)
from app.application.use_cases.pedidos_venda_abertos.resolve_portfolio_scope_use_case import (
    PortfolioScope,
)
from app.domain.ports.pedidos_venda_abertos.pedidos_venda_abertos_query_repository_port import (
    PedidosVendaAbertosQueryRepositoryPort,
)


def _optional_date(value: Any) -> str | None:
    if value is None or value == "":
        return None
    return str(value)


def _as_float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    return float(value)


def _as_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_item(row: dict) -> dict:
    return {
        "nome_cliente": _as_str(row.get("nome_cliente")),
        "tipo_entidade": _as_str(row.get("tipo_entidade")),
        "tipo_pedido": _as_str(row.get("tipo_pedido")),
        "pedido_cliente": _as_str(row.get("pedido_cliente")),
        "filial": _as_str(row.get("filial")),
        "pedido": _as_str(row.get("pedido")),
        "linha": _as_str(row.get("linha")),
        "produto": _as_str(row.get("produto")),
        "codigo_cliente": _as_str(row.get("codigo_cliente")),
        "codigo_cadastro": _as_str(row.get("codigo_cadastro")),
        "loja_cadastro": _as_str(row.get("loja_cadastro")),
        "quantidade": _as_float(row.get("quantidade")),
        "entregue": _as_float(row.get("entregue")),
        "saldo": _as_float(row.get("saldo")),
        "data_despacho": _optional_date(row.get("data_despacho")),
        "data_entrega": _optional_date(row.get("data_entrega")),
        "no_estoque": _as_float(row.get("no_estoque")),
        "preco_venda": _as_float(row.get("preco_venda")),
        "valor_aberto": _as_float(row.get("valor_aberto")),
    }


def _normalize_summary(row: dict) -> PedidosVendaAbertosSummary:
    return PedidosVendaAbertosSummary(
        total_linhas=int(row.get("total_linhas") or 0),
        valor_total_aberto=_as_float(row.get("valor_total_aberto")),
        saldo_total=_as_float(row.get("saldo_total")),
        itens_com_estoque=int(row.get("itens_com_estoque") or 0),
        itens_estoque_parcial=int(row.get("itens_estoque_parcial") or 0),
        itens_sem_estoque=int(row.get("itens_sem_estoque") or 0),
    )


def _recompute_summary(items: list[dict]) -> PedidosVendaAbertosSummary:
    total_linhas = len(items)
    valor_total = 0.0
    saldo_total = 0.0
    com_estoque = 0
    parcial = 0
    sem_estoque = 0
    for item in items:
        valor_total += float(item.get("valor_aberto") or 0)
        saldo_total += float(item.get("saldo") or 0)
        saldo = float(item.get("saldo") or 0)
        estoque = float(item.get("no_estoque") or 0)
        if saldo <= 0:
            continue
        if estoque <= 0:
            sem_estoque += 1
        elif estoque >= saldo:
            com_estoque += 1
        else:
            parcial += 1
    return PedidosVendaAbertosSummary(
        total_linhas=total_linhas,
        valor_total_aberto=valor_total,
        saldo_total=saldo_total,
        itens_com_estoque=com_estoque,
        itens_estoque_parcial=parcial,
        itens_sem_estoque=sem_estoque,
    )


def _item_in_portfolio(item: dict, allowed: frozenset[tuple[str, str]]) -> bool:
    key = (
        _as_str(item.get("codigo_cadastro")),
        _as_str(item.get("loja_cadastro")),
    )
    return key in allowed


class ListPedidosVendaAbertosUseCase:

    def __init__(self, repository: PedidosVendaAbertosQueryRepositoryPort):
        self._repository = repository

    def execute(self, scope: PortfolioScope | None = None) -> ListPedidosVendaAbertosResponse:
        if scope is not None and scope.empty_portfolio:
            return ListPedidosVendaAbertosResponse(
                items=[],
                summary=PedidosVendaAbertosSummary(),
                portfolio_message=scope.message,
                portfolio_empty=True,
                portfolio_seller_id=scope.seller_id,
            )

        raw_items, raw_summary = self._repository.list_open_orders()
        items = [_normalize_item(row) for row in raw_items]

        if scope is None or scope.unrestricted or scope.allowed_customers is None:
            summary = _normalize_summary(raw_summary)
            return ListPedidosVendaAbertosResponse(
                items=items,
                summary=summary,
                portfolio_message=None,
                portfolio_empty=False,
                portfolio_seller_id=scope.seller_id if scope else None,
            )

        filtered = [
            item for item in items if _item_in_portfolio(item, scope.allowed_customers)
        ]
        return ListPedidosVendaAbertosResponse(
            items=filtered,
            summary=_recompute_summary(filtered),
            portfolio_message=scope.message,
            portfolio_empty=False,
            portfolio_seller_id=scope.seller_id,
        )

    def execute_for_customer(
        self,
        customer_code: str,
        customer_store: str,
    ) -> ListPedidosVendaAbertosResponse:
        """Conta 360: linhas do par código/loja sem membership/carteira."""
        code = _as_str(customer_code)
        store = _as_str(customer_store)
        if not code or not store:
            raise ValueError("customer_code e customer_store são obrigatórios.")

        raw_items, raw_summary = self._repository.list_open_orders_for_customer(
            code,
            store,
        )
        items = [_normalize_item(row) for row in raw_items]
        return ListPedidosVendaAbertosResponse(
            items=items,
            summary=_normalize_summary(raw_summary),
            portfolio_message=None,
            portfolio_empty=False,
            portfolio_seller_id=None,
        )
