from unittest.mock import MagicMock

from app.application.use_cases.pedidos_venda_abertos.list_recently_closed_orders_use_case import (
    ListRecentlyClosedOrdersUseCase,
)


def test_list_recently_closed_orders_normalizes_and_marks_completed() -> None:
    repo = MagicMock()
    repo.list_recently_closed.return_value = [
        {
            "nome_cliente": "ACME",
            "filial": "01",
            "pedido": "100",
            "linha": "01",
            "produto": "P1",
            "codigo_cadastro": "C1",
            "loja_cadastro": "01",
            "quantidade": 10,
            "entregue": 10,
            "saldo": 0,
            "preco_venda": 5,
            "valor_aberto": 50,
            "data_entrega": "2026-08-01",
        }
    ]
    result = ListRecentlyClosedOrdersUseCase(repository=repo).execute(days=30)
    assert result["summary"]["total_linhas"] == 1
    assert result["summary"]["days"] == 30
    assert result["items"][0]["kanbanStage"] == "completed"
    assert result["items"][0]["saldo"] == 0.0
    assert "created_by" not in result["items"][0]
    repo.list_recently_closed.assert_called_once_with(days=30)
