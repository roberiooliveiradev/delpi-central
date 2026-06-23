from app.infrastructure.persistence.totvs.production_fabril.production_fabril_oee_kpi_sql import (
    OEE_FABRIL_KPI_AVG_SELECT,
    OEE_FABRIL_KPI_BY_BRANCH_SELECT,
    OEE_FABRIL_KPI_FROM,
)


def test_oee_kpi_sql_uses_nolock_on_fabril_view() -> None:
    for fragment in (
        OEE_FABRIL_KPI_FROM,
        OEE_FABRIL_KPI_AVG_SELECT,
        OEE_FABRIL_KPI_BY_BRANCH_SELECT,
    ):
        assert "vw_Apontamentos_Eficiencia" in fragment
        assert "WITH (NOLOCK)" in fragment


def test_oee_kpi_sql_uses_try_cast_on_efficiency() -> None:
    assert "TRY_CAST(EF.EFICIENCIA_PERCENTUAL AS FLOAT)" in OEE_FABRIL_KPI_AVG_SELECT
    assert "TRY_CAST(EF.EFICIENCIA_PERCENTUAL AS FLOAT)" in OEE_FABRIL_KPI_BY_BRANCH_SELECT
