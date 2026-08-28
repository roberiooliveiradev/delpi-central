"""Repository ops-abertas usa SQL canônico (sem view opaca)."""

from __future__ import annotations

from unittest.mock import patch

from app.infrastructure.persistence.totvs.pedidos_venda_abertos.ops_abertas_query_repository import (
    OpsAbertasQueryRepository,
)
from app.infrastructure.persistence.totvs.pedidos_venda_abertos.ops_abertas_sql import (
    build_ops_abertas_detalhe_sql,
    build_ops_abertas_resumo_sql,
)


def test_ops_repository_executes_canonical_sql() -> None:
    repository = OpsAbertasQueryRepository()
    detalhe = build_ops_abertas_detalhe_sql()
    resumo = build_ops_abertas_resumo_sql()

    with patch.object(repository, "_connect"):
        with patch.object(repository, "execute_query") as mock_execute:
            mock_execute.side_effect = [
                [{"filial": "01", "numero_op": "1", "saldo_op": 10, "produto": "X"}],
                [{"filial": "01", "produto": "X", "saldo_total_ops": 10}],
            ]
            with repository:
                items, summary = repository.list_open_ops()

    assert len(items) == 1
    assert len(summary) == 1
    assert mock_execute.call_count == 2
    first_sql = mock_execute.call_args_list[0].args[0]
    second_sql = mock_execute.call_args_list[1].args[0]
    assert first_sql == detalhe
    assert second_sql == resumo
    assert "VW_OPS_ABERTAS_PRODUTO" not in first_sql
    assert "OP.C2_QUANT > OP.C2_QUJE" in first_sql
    assert "C2_DATRF" in first_sql
