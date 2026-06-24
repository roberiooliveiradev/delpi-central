from app.infrastructure.persistence.totvs.production_fabril.production_fabril_ef_items_sql import (
    build_ef_fabril_items_list_sql,
    build_fabril_sh6010_ranked_cte,
)


def test_fabril_sh6010_ranked_cte_filters_by_period_and_branches() -> None:
    cte, params = build_fabril_sh6010_ranked_cte(
        date_start="2026-04-01",
        date_end="2026-06-30",
        branch=None,
        branches=("01", "02"),
    )

    assert "H6_RANKED AS" in cte
    assert "SH6010 H6 WITH (NOLOCK)" in cte
    assert "ROW_NUMBER()" in cte
    assert params == ("2026-04-01", "2026-06-30", "01", "02")


def test_ef_fabril_items_list_sql_uses_ranked_cte_instead_of_outer_apply() -> None:
    sql, params = build_ef_fabril_items_list_sql(
        where_clause="EF.FILIAL = ?",
        where_params=("01",),
        date_start="2026-04-01",
        date_end="2026-06-30",
        branch="01",
        branches=("01", "02"),
    )

    assert "WITH" in sql
    assert "H6_RANKED AS" in sql
    assert "LEFT JOIN H6_RANKED H6" in sql
    assert "OUTER APPLY" not in sql
    assert "EF.FILIAL AS FILIAL" in sql
    assert params == ("2026-04-01", "2026-06-30", "01", "01")
