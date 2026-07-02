from app.infrastructure.persistence.totvs.production_fabril.production_fabril_oee_kpi_sql import (
    OEE_FABRIL_KPI_AVG_SELECT,
    OEE_FABRIL_KPI_BY_BRANCH_SELECT,
    OEE_FABRIL_KPI_BY_DAY_AND_BRANCH_SELECT,
    OEE_FABRIL_KPI_FROM,
)


def test_oee_kpi_sql_uses_nolock_on_fabril_view() -> None:
    for fragment in (
        OEE_FABRIL_KPI_FROM,
        OEE_FABRIL_KPI_AVG_SELECT,
        OEE_FABRIL_KPI_BY_BRANCH_SELECT,
        OEE_FABRIL_KPI_BY_DAY_AND_BRANCH_SELECT,
    ):
        assert "vw_Apontamentos_Eficiencia" in fragment
        assert "WITH (NOLOCK)" in fragment


def test_oee_kpi_sql_uses_try_cast_on_efficiency() -> None:
    assert "TRY_CAST(EF.EFICIENCIA_PERCENTUAL AS FLOAT)" in OEE_FABRIL_KPI_AVG_SELECT
    assert "TRY_CAST(EF.EFICIENCIA_PERCENTUAL AS FLOAT)" in OEE_FABRIL_KPI_BY_BRANCH_SELECT


def test_oee_kpi_by_branch_groups_on_raw_filial_column() -> None:
    assert "GROUP BY EF.FILIAL" not in OEE_FABRIL_KPI_BY_BRANCH_SELECT
    assert "RTRIM(LTRIM(EF.FILIAL)) AS branch" in OEE_FABRIL_KPI_BY_BRANCH_SELECT


def test_oee_kpi_by_day_exposes_raw_components_for_period_derivation() -> None:
    # Componentes brutos permitem derivar o KPI por filial do período
    # a partir da mesma agregação diária (um único scan da view fabril).
    assert (
        "SUM(TRY_CAST(EF.EFICIENCIA_PERCENTUAL AS FLOAT)) AS efficiency_sum"
        in OEE_FABRIL_KPI_BY_DAY_AND_BRANCH_SELECT
    )
    assert (
        "COUNT(TRY_CAST(EF.EFICIENCIA_PERCENTUAL AS FLOAT)) AS efficiency_sample_count"
        in OEE_FABRIL_KPI_BY_DAY_AND_BRANCH_SELECT
    )
