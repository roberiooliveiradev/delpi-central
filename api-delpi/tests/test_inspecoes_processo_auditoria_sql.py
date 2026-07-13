"""Sanidade do SQL de auditoria apontamento × inspeção."""

from __future__ import annotations

from app.domain.production.production_fabril_appointment_scope import (
    EXCLUDED_WORK_CENTERS,
)
from app.infrastructure.persistence.totvs.inspecoes_processo.inspecoes_processo_auditoria_sql import (
    AUDITORIA_APONTAMENTOS_BASE_SQL,
    AUDITORIA_ENSAIADOR_MAP_SQL,
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
    sql = build_qpr_for_ops_sql(3)
    assert "QPR010" in sql
    assert "QPR_ENSR" in sql
    assert sql.count("QPR.QPR_OP LIKE ?") == 3
