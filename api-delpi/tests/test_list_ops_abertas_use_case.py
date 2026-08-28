from unittest.mock import MagicMock

from app.application.use_cases.pedidos_venda_abertos.list_ops_abertas_use_case import (
    ListOpsAbertasUseCase,
)


def test_list_ops_abertas_normalizes_items_and_resumo() -> None:
    repository = MagicMock()
    repository.list_open_ops.return_value = (
        [
            {
                "filial": "01",
                "numero_op": "123456/01/001",
                "produto": "10080022",
                "descricao_produto": "Produto exemplo",
                "tipo_produto": "PA",
                "quantidade_op": 100,
                "quantidade_produzida": 40,
                "saldo_op": 60,
                "data_emissao_op": "2026-06-01",
                "data_inicio_prevista_op": "2026-06-03",
                "data_fim_prevista_op": "2026-06-10",
                "armazem": "01",
                "observacao_op": "Prioridade cliente X",
            }
        ],
        [
            {
                "filial": "01",
                "produto": "10080022",
                "descricao_produto": "Produto exemplo",
                "tipo_produto": "PA",
                "quantidade_ops_abertas": 2,
                "quantidade_total_ops": 150,
                "quantidade_total_produzida": 50,
                "saldo_total_ops": 100,
                "primeira_data_prevista_op": "2026-06-10",
                "ultima_data_prevista_op": "2026-06-20",
            }
        ],
    )

    use_case = ListOpsAbertasUseCase(repository)
    result = use_case.execute()

    repository.list_open_ops.assert_called_once()
    assert len(result.items) == 1
    assert result.items[0]["numero_op"] == "123456/01/001"
    assert result.items[0]["saldo_op"] == 60.0
    assert result.items[0]["observacao_op"] == "Prioridade cliente X"
    assert len(result.resumo) == 1


def test_list_ops_abertas_normalizes_null_dates() -> None:
    repository = MagicMock()
    repository.list_open_ops.return_value = (
        [
            {
                "filial": "01",
                "numero_op": "999/01/001",
                "produto": "X",
                "descricao_produto": "",
                "tipo_produto": "PA",
                "quantidade_op": 10,
                "quantidade_produzida": 0,
                "saldo_op": 10,
                "data_emissao_op": "",
                "data_inicio_prevista_op": None,
                "data_fim_prevista_op": "",
                "armazem": "01",
            }
        ],
        [],
    )

    result = ListOpsAbertasUseCase(repository).execute()

    assert result.items[0]["data_emissao_op"] is None
    assert result.items[0]["data_fim_prevista_op"] is None
