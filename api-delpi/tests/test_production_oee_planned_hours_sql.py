"""Regressão — OEE planned hours via HY_TEMPAD × qtd (não TEMPOM × qtd/C2)."""

from app.infrastructure.persistence.totvs.production_repositories.production_oee_sql import (
    OEE_PLANNED_HOURS_EXPR,
    OEE_STANDARD_TIME_FACTOR_EXPR,
)


def test_oee_standard_time_prefers_hy_tempad() -> None:
    assert "SHY.HY_TEMPAD" in OEE_STANDARD_TIME_FACTOR_EXPR
    assert "SHY.HY_TEMPOM" in OEE_STANDARD_TIME_FACTOR_EXPR
    assert "SHY.HY_QUANT" in OEE_STANDARD_TIME_FACTOR_EXPR
    assert "G2_TEMPAD" in OEE_STANDARD_TIME_FACTOR_EXPR
    assert "/ 1000.0" not in OEE_STANDARD_TIME_FACTOR_EXPR


def test_oee_planned_hours_is_setup_plus_unit_times_qty() -> None:
    assert "H6.H6_QTDPROD" in OEE_PLANNED_HOURS_EXPR
    assert "C2_QUANT" not in OEE_PLANNED_HOURS_EXPR
    # Anti-padrão legado: TEMPOM × (qtd / C2).
    assert "/ NULLIF(TRY_CAST(REPLACE(LTRIM(RTRIM(SC2.C2_QUANT))" not in OEE_PLANNED_HOURS_EXPR
