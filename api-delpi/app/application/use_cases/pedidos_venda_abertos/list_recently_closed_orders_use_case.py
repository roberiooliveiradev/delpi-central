"""List recently closed sales-order lines for Kanban completed column."""

from __future__ import annotations

from typing import Any

from app.infrastructure.persistence.totvs.pedidos_venda_abertos.recently_closed_orders_query_repository import (
    RecentlyClosedOrdersQueryRepository,
)


def _as_float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _as_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _optional_date(value: Any) -> str | None:
    text = _as_str(value)
    return text or None


def _normalize_item(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "nome_cliente": _as_str(row.get("nome_cliente")),
        "tipo_entidade": _as_str(row.get("tipo_entidade")) or "CLIENTE",
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
        "saldo": 0.0,
        "data_despacho": _optional_date(row.get("data_despacho")),
        "data_entrega": _optional_date(row.get("data_entrega")),
        "no_estoque": 0.0,
        "preco_venda": _as_float(row.get("preco_venda")),
        "valor_aberto": _as_float(row.get("valor_aberto")),
        "kanbanStage": "completed",
    }


class ListRecentlyClosedOrdersUseCase:
    def __init__(self, repository: RecentlyClosedOrdersQueryRepository | None = None):
        self._repository = repository or RecentlyClosedOrdersQueryRepository()

    def execute(self, *, days: int = 30) -> dict[str, Any]:
        rows = self._repository.list_recently_closed(days=days)
        items = [_normalize_item(row) for row in rows]
        return {
            "items": items,
            "summary": {
                "total_linhas": len(items),
                "valor_total": sum(_as_float(i.get("valor_aberto")) for i in items),
                "days": max(1, min(int(days or 30), 90)),
            },
        }
