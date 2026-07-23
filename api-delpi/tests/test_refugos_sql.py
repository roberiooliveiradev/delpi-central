from app.infrastructure.persistence.totvs.refugos.refugos_sql import (
    build_base_where,
    build_ranking_query,
    build_resumo_query,
    build_serie_query,
)


def test_base_where_filters_refugo_branch_and_closed_open_dates() -> None:
    where, params = build_base_where(
        date_start="20260401",
        date_end_exclusive="20260428",
        branch="01",
    )

    assert "BC.D_E_L_E_T_ = ''" in where
    assert "BC.BC_TIPO = ?" in where
    assert "LTRIM(RTRIM(BC.BC_FILIAL)) = ?" in where
    assert "BC.BC_DATA >= ?" in where
    assert "BC.BC_DATA < ?" in where
    assert params == ["R", "01", "20260401", "20260428"]


def test_base_where_consolidated_uses_valid_branch_in_clause() -> None:
    where, params = build_base_where(
        date_start="20260401",
        date_end_exclusive="20260428",
        branch=None,
    )

    assert "LTRIM(RTRIM(BC.BC_FILIAL)) IN (?, ?)" in where
    assert params == ["R", "01", "02", "20260401", "20260428"]


def test_resumo_query_uses_nolock_and_avg_cost_join() -> None:
    query, params = build_resumo_query(
        date_start="20260401",
        date_end_exclusive="20260428",
        branch="01",
        day_start="20260427",
        day_end_exclusive="20260428",
        month_start="20260401",
        month_end_exclusive="20260428",
    )

    assert "SBC010 BC WITH (NOLOCK)" in query
    assert "SB2010 WITH (NOLOCK)" in query
    assert "AVG(NULLIF(CAST(B2_CM1 AS FLOAT), 0))" in query
    assert "CYO010" in query
    assert "SYS_USR" in query
    assert params[12] == "R"
    assert params[13] == "01"


def test_ranking_motivo_groups_by_cyo_label() -> None:
    query, params = build_ranking_query(
        dimension="motivo",
        date_start="20260401",
        date_end_exclusive="20260428",
        branch="01",
        limit=10,
    )

    assert "CYO_DSRF" in query
    assert "GROUP BY" in query
    assert "ORDER BY value DESC" in query
    assert "TOP 10" in query
    assert params[0] == "R"


def test_serie_day_groups_by_yyyymmdd() -> None:
    query, params = build_serie_query(
        granularity="day",
        date_start="20260701",
        date_end_exclusive="20260716",
        branch="01",
    )

    assert "LEFT(LTRIM(RTRIM(BC.BC_DATA)), 8) AS bucket" in query
    assert "GROUP BY LEFT(LTRIM(RTRIM(BC.BC_DATA)), 8)" in query
    assert "ORDER BY bucket ASC" in query
    assert params == ("R", "01", "20260701", "20260716")


def test_serie_month_groups_by_yyyymm() -> None:
    query, _params = build_serie_query(
        granularity="month",
        date_start="20260101",
        date_end_exclusive="20260716",
        branch="02",
    )

    assert "LEFT(LTRIM(RTRIM(BC.BC_DATA)), 6) AS bucket" in query


def test_registros_query_exposes_unit_cost_and_pa_description() -> None:
    from app.infrastructure.persistence.totvs.refugos.refugos_sql import (
        build_registros_query,
    )

    query, _params = build_registros_query(
        date_start="20260701",
        date_end_exclusive="20260716",
        branch="01",
        offset=0,
        page_size=25,
    )

    assert "AS unit_cost" in query
    assert "AS finished_product_desc" in query
