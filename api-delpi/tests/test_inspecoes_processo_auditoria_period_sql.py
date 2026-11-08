"""Regression tests for process-inspection audit production-date filtering."""

from app.infrastructure.persistence.totvs.inspecoes_processo.inspecoes_processo_auditoria_sql import (
    build_auditoria_apontamentos_base_sql,
    build_auditoria_ensaiador_map_sql,
    build_qpr_for_ops_sql,
    build_qpk_for_ops_sql,
)


def test_audit_dates_are_inclusive_and_query_parameterized() -> None:
    sql, branch_params = build_auditoria_apontamentos_base_sql("02")
    assert "EF.DATA_PRODUCAO >= ?" in sql
    assert "EF.DATA_PRODUCAO < DATEADD(day, 1, CAST(? AS DATE))" in sql
    assert sql.count("?") == len(branch_params) + 2
    assert "STATUS_REGISTRO" in sql


def test_audit_lookups_expose_branch_for_join_keys() -> None:
    sql, _ = build_auditoria_ensaiador_map_sql("02")
    assert "AS Filial" in sql
    for builder in (build_qpr_for_ops_sql, build_qpk_for_ops_sql):
        text, params = builder(2, "02")
        assert "AS Filial" in text
        assert len(params) <= 1
