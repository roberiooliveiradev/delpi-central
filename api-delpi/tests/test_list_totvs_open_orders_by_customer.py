"""Pedidos em aberto por cliente (Conta 360) — sem dump global."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.application.use_cases.pedidos_venda_abertos.list_pedidos_venda_abertos_use_case import (
    ListPedidosVendaAbertosUseCase,
)


def test_execute_for_customer_maps_items_and_summary() -> None:
    repository = MagicMock()
    repository.list_open_orders_for_customer.return_value = (
        [
            {
                "nome_cliente": "ACME",
                "tipo_entidade": "CLIENTE",
                "tipo_pedido": "N",
                "pedido_cliente": "",
                "filial": "01",
                "pedido": "102723",
                "linha": "03",
                "produto": "90A",
                "codigo_cliente": "",
                "codigo_cadastro": "000001",
                "loja_cadastro": "06",
                "quantidade": 10,
                "entregue": 0,
                "saldo": 10,
                "data_despacho": None,
                "data_entrega": "2026-07-31",
                "no_estoque": 0,
                "preco_venda": 10,
                "valor_aberto": 100,
            }
        ],
        {
            "total_linhas": 1,
            "valor_total_aberto": 100,
            "saldo_total": 10,
            "itens_com_estoque": 0,
            "itens_estoque_parcial": 0,
            "itens_sem_estoque": 1,
        },
    )

    result = ListPedidosVendaAbertosUseCase(repository).execute_for_customer(
        "000001",
        "06",
    )

    repository.list_open_orders_for_customer.assert_called_once_with("000001", "06")
    assert len(result.items) == 1
    assert result.items[0]["pedido"] == "102723"
    assert result.summary.total_linhas == 1
    assert result.portfolio_empty is False


def test_execute_for_customer_requires_identity() -> None:
    repository = MagicMock()
    use_case = ListPedidosVendaAbertosUseCase(repository)
    try:
        use_case.execute_for_customer(" ", "01")
        raised = False
    except ValueError:
        raised = True
    assert raised
    repository.list_open_orders_for_customer.assert_not_called()
