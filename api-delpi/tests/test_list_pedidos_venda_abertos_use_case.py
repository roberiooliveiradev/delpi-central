from unittest.mock import MagicMock

from app.application.use_cases.pedidos_venda_abertos.list_pedidos_venda_abertos_use_case import (
    ListPedidosVendaAbertosUseCase,
)


def test_list_pedidos_venda_abertos_normalizes_items_and_summary() -> None:
    repository = MagicMock()
    repository.list_open_orders.return_value = (
        [
            {
                "nome_cliente": "CLIENTE A",
                "tipo_entidade": "CLIENTE",
                "tipo_pedido": "N",
                "pedido_cliente": "PO-1",
                "filial": "01",
                "pedido": "100",
                "linha": "01",
                "produto": "90300079",
                "codigo_cliente": "PN-903",
                "codigo_cadastro": "10047758",
                "loja_cadastro": "11",
                "quantidade": 10,
                "entregue": 4,
                "saldo": 6,
                "data_despacho": "",
                "data_entrega": "2026-06-09",
                "no_estoque": 2,
                "preco_venda": 100.5,
                "valor_aberto": 603.0,
            }
        ],
        {
            "total_linhas": 1,
            "valor_total_aberto": 603.0,
            "saldo_total": 6,
            "itens_com_estoque": 0,
            "itens_estoque_parcial": 1,
            "itens_sem_estoque": 0,
        },
    )

    use_case = ListPedidosVendaAbertosUseCase(repository)
    result = use_case.execute()

    repository.list_open_orders.assert_called_once()
    assert len(result.items) == 1
    assert result.items[0]["data_despacho"] is None
    assert result.items[0]["data_entrega"] == "2026-06-09"
    assert result.items[0]["saldo"] == 6.0
    assert result.summary.total_linhas == 1
    assert result.summary.itens_estoque_parcial == 1

    payload = result.to_dict()
    assert payload["summary"]["valor_total_aberto"] == 603.0
    assert payload["items"][0]["nome_cliente"] == "CLIENTE A"
    assert payload["items"][0]["codigo_cliente"] == "PN-903"
    assert payload["items"][0]["codigo_cadastro"] == "10047758"
    assert payload["items"][0]["loja_cadastro"] == "11"
    assert payload["portfolio"]["empty"] is False


def test_open_order_item_contract_excludes_created_by() -> None:
    """SC5 has no human-resolvable creator — do not expose created_by or C5_MSUIDT."""
    repository = MagicMock()
    repository.list_open_orders.return_value = (
        [
            {
                "nome_cliente": "CLIENTE A",
                "tipo_entidade": "CLIENTE",
                "tipo_pedido": "N",
                "pedido_cliente": "PO-1",
                "filial": "01",
                "pedido": "100",
                "linha": "01",
                "produto": "90300079",
                "codigo_cliente": "PN-903",
                "codigo_cadastro": "10047758",
                "loja_cadastro": "11",
                "quantidade": 10,
                "entregue": 4,
                "saldo": 6,
                "data_despacho": None,
                "data_entrega": "2026-06-09",
                "no_estoque": 2,
                "preco_venda": 100.5,
                "valor_aberto": 603.0,
                "created_by": "should-be-stripped",
                "C5_MSUIDT": "F19724C3-FAF9-4745-B8F6-A74BE8FD1E97",
            }
        ],
        {
            "total_linhas": 1,
            "valor_total_aberto": 603.0,
            "saldo_total": 6,
            "itens_com_estoque": 0,
            "itens_estoque_parcial": 1,
            "itens_sem_estoque": 0,
        },
    )

    item = ListPedidosVendaAbertosUseCase(repository).execute().items[0]
    assert "created_by" not in item
    assert "C5_MSUIDT" not in item
    assert "msuidt" not in item
