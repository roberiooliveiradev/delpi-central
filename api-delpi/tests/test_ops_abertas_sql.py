"""Regressão — predicado Delpi de OP aberta em ops-abertas."""

from __future__ import annotations

from app.infrastructure.persistence.totvs.pedidos_venda_abertos.ops_abertas_sql import (
    build_ops_abertas_detalhe_sql,
    build_ops_abertas_resumo_sql,
)


def test_ops_abertas_detalhe_sql_excludes_finished_partial() -> None:
    sql = build_ops_abertas_detalhe_sql()
    assert "SC2010" in sql
    assert "OP.C2_QUANT > OP.C2_QUJE" in sql
    assert "C2_DATRF" in sql
    assert "LTRIM(RTRIM(OP.C2_DATRF)) = ''" in sql
    assert "B1_TIPO" in sql
    assert "VW_OPS_ABERTAS_PRODUTO" not in sql
    assert "saldo_op" in sql
    assert "numero_op" in sql


def test_ops_abertas_resumo_sql_same_open_predicate() -> None:
    sql = build_ops_abertas_resumo_sql()
    assert "OP.C2_QUANT > OP.C2_QUJE" in sql
    assert "C2_DATRF" in sql
    assert "VW_OPS_ABERTAS_PRODUTO_RESUMO" not in sql
    assert "GROUP BY" in sql
    assert "saldo_total_ops" in sql
