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
                "unidade": "MI",
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
    assert result.items[0]["unidade"] == "MI"
    assert result.summary.total_linhas == 1
    assert result.summary.itens_estoque_parcial == 1

    payload = result.to_dict()
    assert payload["summary"]["valor_total_aberto"] == 603.0
    assert payload["items"][0]["nome_cliente"] == "CLIENTE A"
    assert payload["items"][0]["codigo_cliente"] == "PN-903"
    assert payload["items"][0]["codigo_cadastro"] == "10047758"
    assert payload["items"][0]["loja_cadastro"] == "11"
    assert payload["items"][0]["unidade"] == "MI"
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


def test_list_open_orders_preserves_supplier_and_customer_entities() -> None:
    """Regressão TRAMAR/AGC: Meus Pedidos mantém FORNECEDOR com nome/tipo da
    entidade real — código/loja colidindo com SA1 não troca a identidade."""
    supplier_row = {
        "nome_cliente": "TRAMAR",
        "tipo_entidade": "FORNECEDOR",
        "tipo_pedido": "B",
        "pedido_cliente": "",
        "filial": "02",
        "pedido": "002668",
        "linha": "01",
        "produto": "20050012",
        "codigo_cliente": "",
        "codigo_cadastro": "000006",
        "loja_cadastro": "01",
        "quantidade": 776,
        "entregue": 345,
        "saldo": 431,
        "unidade": "PC",
        "data_despacho": None,
        "data_entrega": "2026-10-02",
        "no_estoque": 0,
        "preco_venda": 5.0,
        "valor_aberto": 2155.0,
    }
    customer_row = dict(
        supplier_row,
        nome_cliente="AGC",
        tipo_entidade="CLIENTE",
        tipo_pedido="N",
        pedido="102700",
        valor_aberto=500.0,
    )
    repository = MagicMock()
    repository.list_open_orders.return_value = (
        [supplier_row, customer_row],
        {"total_linhas": 2, "valor_total_aberto": 2655.0, "saldo_total": 0,
         "itens_com_estoque": 0, "itens_estoque_parcial": 0,
         "itens_sem_estoque": 2},
    )

    result = ListPedidosVendaAbertosUseCase(repository).execute()

    assert len(result.items) == 2
    supplier = next(i for i in result.items if i["pedido"] == "002668")
    assert supplier["tipo_entidade"] == "FORNECEDOR"
    assert supplier["nome_cliente"] == "TRAMAR"
    assert supplier["codigo_cadastro"] == "000006"
    assert supplier["loja_cadastro"] == "01"
    assert supplier["valor_aberto"] == 2155.0
    customer = next(i for i in result.items if i["pedido"] == "102700")
    assert customer["tipo_entidade"] == "CLIENTE"
    assert customer["nome_cliente"] == "AGC"
