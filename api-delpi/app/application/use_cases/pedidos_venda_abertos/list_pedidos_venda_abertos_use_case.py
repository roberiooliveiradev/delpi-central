from __future__ import annotations

from typing import Any

from app.application.dto.pedidos_venda_abertos.list_pedidos_venda_abertos_response import (
    ListPedidosVendaAbertosResponse,
    PedidosVendaAbertosSummary,
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


class ListPedidosVendaAbertosUseCase:

    def __init__(self, repository: PedidosVendaAbertosQueryRepositoryPort):
        self._repository = repository

    def execute(self) -> ListPedidosVendaAbertosResponse:
        raw_items, raw_summary = self._repository.list_open_orders()
        items = [_normalize_item(row) for row in raw_items]
        summary = _normalize_summary(raw_summary)
        return ListPedidosVendaAbertosResponse(items=items, summary=summary)
