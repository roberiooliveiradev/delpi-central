"""Filtra payload TOTVS de pedidos em aberto pelo escopo commercial (BFF)."""

from __future__ import annotations

from typing import Any

from commercial_app.application.services.resolve_commercial_customer_scope_service import (
    CommercialCustomerScope,
)


def _as_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _as_float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    return float(value)


def _item_in_scope(item: dict[str, Any], allowed: frozenset[tuple[str, str]]) -> bool:
    key = (_as_str(item.get("codigo_cadastro")), _as_str(item.get("loja_cadastro")))
    return key in allowed


def _recompute_summary(items: list[dict[str, Any]]) -> dict[str, Any]:
    total_linhas = len(items)
    valor_total = 0.0
    saldo_total = 0.0
    com_estoque = 0
    parcial = 0
    sem_estoque = 0
    for item in items:
        valor_total += _as_float(item.get("valor_aberto"))
        saldo_total += _as_float(item.get("saldo"))
        saldo = _as_float(item.get("saldo"))
        estoque = _as_float(item.get("no_estoque"))
        if saldo <= 0:
            continue
        if estoque <= 0:
            sem_estoque += 1
        elif estoque >= saldo:
            com_estoque += 1
        else:
            parcial += 1
    return {
        "total_linhas": total_linhas,
        "valor_total_aberto": valor_total,
        "saldo_total": saldo_total,
        "itens_com_estoque": com_estoque,
        "itens_estoque_parcial": parcial,
        "itens_sem_estoque": sem_estoque,
    }


class FilterOpenOrdersByScopeService:
    """Aplica allowlist de clientes sobre data da api-delpi (sem membership na api-delpi)."""

    def apply(
        self,
        data: dict[str, Any] | None,
        scope: CommercialCustomerScope,
    ) -> dict[str, Any]:
        base = dict(data or {})
        # Irrestrito (ex.: for_open_orders sem carteira) prevalece sobre empty_portfolio.
        if scope.unrestricted or scope.allowed_customers is None:
            portfolio = base.get("portfolio") if isinstance(base.get("portfolio"), dict) else {}
            return {
                **base,
                "portfolio": {
                    "empty": False,
                    "message": None,
                    "seller_id": scope.portfolio_id or (portfolio.get("seller_id") if portfolio else None),
                },
            }

        if scope.empty_portfolio:
            empty_summary = _recompute_summary([])
            return {
                "items": [],
                "summary": empty_summary,
                "portfolio": {
                    "empty": True,
                    "message": scope.message,
                    "seller_id": scope.portfolio_id,
                },
            }

        items_raw = base.get("items")
        items = [item for item in items_raw if isinstance(item, dict)] if isinstance(items_raw, list) else []
        filtered = [
            item for item in items if _item_in_scope(item, scope.allowed_customers)
        ]
        return {
            "items": filtered,
            "summary": _recompute_summary(filtered),
            "portfolio": {
                "empty": False,
                "message": scope.message,
                "seller_id": scope.portfolio_id,
            },
        }
