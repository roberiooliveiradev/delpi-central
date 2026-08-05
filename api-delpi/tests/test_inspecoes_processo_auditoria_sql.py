"""Sanidade do SQL de auditoria apontamento × inspeção."""

from __future__ import annotations

from app.domain.production.production_fabril_appointment_scope import (
    EXCLUDED_WORK_CENTERS,
)
from app.infrastructure.persistence.totvs.inspecoes_processo.inspecoes_processo_auditoria_sql import (
    AUDITORIA_APONTAMENTOS_BASE_SQL,
    AUDITORIA_ENSAIADOR_MAP_SQL,
    build_inspecao_cadastrada_for_product_revisions_sql,
    build_qpk_for_ops_sql,
    build_qpr_for_ops_sql,
)


def test_auditoria_base_sql_uses_ef_view_and_excluded_cts() -> None:
    sql = AUDITORIA_APONTAMENTOS_BASE_SQL
    assert "vw_Apontamentos_Eficiencia" in sql
    for ct in EXCLUDED_WORK_CENTERS:
        assert ct in sql


def test_auditoria_ensaiador_map_sql_uses_por_ensaiador() -> None:
    assert "por_ensaiador" in AUDITORIA_ENSAIADOR_MAP_SQL
    assert "Login_Ensaiador" in AUDITORIA_ENSAIADOR_MAP_SQL


def test_build_qpr_for_ops_sql_uses_ensr_and_like_params() -> None:
    sql, branch_params = build_qpr_for_ops_sql(3)
    assert branch_params == ["01"]
    assert "QPR010" in sql
    assert "QPR_ENSR" in sql
    assert sql.count("QPR.QPR_OP LIKE ?") == 3
    assert "QPR.QPR_FILIAL = ?" in sql


def test_build_qpk_for_ops_sql_uses_revisao() -> None:
    sql, branch_params = build_qpk_for_ops_sql(2, "02")
    assert branch_params == ["02"]
    assert "QPK010" in sql
    assert "QPK_REVI" in sql
    assert sql.count("QPK.QPK_OP LIKE ?") == 2


def test_build_inspecao_cadastrada_for_product_revisions_sql_uses_qp7_qp8() -> None:
    sql = build_inspecao_cadastrada_for_product_revisions_sql(2)
    assert "QP7010" in sql
    assert "QP8010" in sql
    assert "QP6010" not in sql
    assert sql.count("RTRIM(QP7.QP7_PRODUT) = ? AND QP7.QP7_REVI = ?") == 2
    assert sql.count("RTRIM(QP8.QP8_PRODUT) = ? AND QP8.QP8_REVI = ?") == 2
    assert "Revisao" in sql
    assert "Operacao" in sql
