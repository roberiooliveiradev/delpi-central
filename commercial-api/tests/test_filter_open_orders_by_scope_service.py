"""Filtro BFF de pedidos em aberto por escopo commercial."""

from __future__ import annotations

from commercial_app.application.services.filter_open_orders_by_scope_service import (
    FilterOpenOrdersByScopeService,
)
from commercial_app.application.services.resolve_commercial_customer_scope_service import (
    CommercialCustomerScope,
)


def test_filter_open_orders_empty_portfolio() -> None:
    scope = CommercialCustomerScope(
        unrestricted=False,
        allowed_customers=frozenset(),
        empty_portfolio=True,
        message="vazia",
        portfolio_id="p1",
    )
    data = FilterOpenOrdersByScopeService().apply(
        {"items": [{"codigo_cadastro": "100", "loja_cadastro": "01", "valor_aberto": 10}]},
        scope,
    )
    assert data["items"] == []
    assert data["summary"]["total_linhas"] == 0
    assert data["portfolio"]["empty"] is True
    assert data["portfolio"]["message"] == "vazia"


def test_filter_open_orders_membership() -> None:
    scope = CommercialCustomerScope(
        unrestricted=False,
        allowed_customers=frozenset({("100", "01")}),
    )
    data = FilterOpenOrdersByScopeService().apply(
        {
            "items": [
                {
                    "codigo_cadastro": "100",
                    "loja_cadastro": "01",
                    "valor_aberto": 10,
                    "saldo": 2,
                    "no_estoque": 2,
                },
                {
                    "codigo_cadastro": "999",
                    "loja_cadastro": "01",
                    "valor_aberto": 99,
                    "saldo": 1,
                    "no_estoque": 0,
                },
            ]
        },
        scope,
    )
    assert len(data["items"]) == 1
    assert data["items"][0]["codigo_cadastro"] == "100"
    assert data["summary"]["total_linhas"] == 1
    assert data["summary"]["valor_total_aberto"] == 10.0


def test_filter_open_orders_unrestricted_keeps_items() -> None:
    scope = CommercialCustomerScope(unrestricted=True, allowed_customers=None)
    raw = {
        "items": [{"codigo_cadastro": "1", "loja_cadastro": "01"}],
        "summary": {"total_linhas": 1},
    }
    data = FilterOpenOrdersByScopeService().apply(raw, scope)
    assert len(data["items"]) == 1
