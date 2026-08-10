from app.infrastructure.persistence.totvs.production_fabril.production_fabril_efficiency_sql import (
    FABRIL_EFICIENCIA_PERCENTUAL_SQL,
    FABRIL_KPI_EFFICIENCY_ALIAS,
)
from app.infrastructure.persistence.totvs.production_fabril.production_fabril_oee_kpi_sql import (
    OEE_FABRIL_KPI_AVG_SELECT,
    OEE_FABRIL_KPI_BY_BRANCH_SELECT,
    OEE_FABRIL_KPI_BY_DAY_AND_BRANCH_SELECT,
    OEE_FABRIL_KPI_FROM,
    build_oee_fabril_kpi_avg_sql,
    build_oee_fabril_kpi_by_day_and_branch_sql,
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


def test_oee_kpi_sql_uses_canonical_tempad_efficiency_not_view_raw() -> None:
    assert "HY_TEMPAD" in FABRIL_EFICIENCIA_PERCENTUAL_SQL
    assert "EF.QTD_APONTADA" in FABRIL_EFICIENCIA_PERCENTUAL_SQL
    assert "TRY_CAST(EF.EFICIENCIA_PERCENTUAL AS FLOAT)" not in OEE_FABRIL_KPI_AVG_SELECT
    assert "TRY_CAST(EF.EFICIENCIA_PERCENTUAL AS FLOAT)" not in OEE_FABRIL_KPI_BY_BRANCH_SELECT
    assert FABRIL_KPI_EFFICIENCY_ALIAS in OEE_FABRIL_KPI_AVG_SELECT
    assert "SHY_RANKED" in OEE_FABRIL_KPI_FROM or "SHY" in OEE_FABRIL_KPI_FROM


def test_oee_kpi_by_branch_groups_on_branch_alias() -> None:
    assert "GROUP BY EF.FILIAL" not in OEE_FABRIL_KPI_BY_BRANCH_SELECT
    assert "RTRIM(LTRIM(EF.FILIAL)) AS branch" in OEE_FABRIL_KPI_BY_BRANCH_SELECT


def test_oee_kpi_by_day_exposes_raw_components_for_period_derivation() -> None:
    assert "efficiency_sum" in OEE_FABRIL_KPI_BY_DAY_AND_BRANCH_SELECT
    assert "efficiency_sample_count" in OEE_FABRIL_KPI_BY_DAY_AND_BRANCH_SELECT
    assert "HY_TEMPAD" in OEE_FABRIL_KPI_BY_DAY_AND_BRANCH_SELECT


def test_build_oee_kpi_avg_sql_joins_shy_sg2_and_filters_valid_range() -> None:
    sql, params = build_oee_fabril_kpi_avg_sql(
        where_clause="EF.DATA_PRODUCAO >= ? AND EF.DATA_PRODUCAO <= ?",
        where_params=("2026-07-01", "2026-07-31"),
        branch="01",
    )
    assert "SHY_RANKED" in sql
    assert "SG2_RANKED" in sql
    assert "SHY010" in sql
    assert "HY_TEMPAD" in sql
    assert "efficiency_pct" in sql
    assert "BETWEEN" not in sql or "<= 199" in sql or "AND efficiency_pct <=" in sql
    assert "efficiency_pct IS NOT NULL" in sql
    assert "efficiency_pct <= 199" in sql
    assert params[:2] == ("01", "01")  # SHY + SG2 branch
    assert params[-2:] == ("2026-07-01", "2026-07-31")


def test_build_oee_kpi_by_day_sql_orders_and_groups() -> None:
    sql, _params = build_oee_fabril_kpi_by_day_and_branch_sql(
        where_clause="1=1",
        where_params=(),
        branch=None,
    )
    assert "GROUP BY production_date, branch" in sql
    assert "ORDER BY production_date, branch" in sql
    assert "efficiency_sum" in sql
