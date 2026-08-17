"""SQL — datas distintas de NC (QI2) para o streak."""

from __future__ import annotations

from app.infrastructure.persistence.totvs.nonconformity_repositories.nonconformity_occurrence_sql import (
    build_occurrence_dates_query,
)


def test_occurrence_dates_sql_filters_customer_without_all_branch() -> None:
    sql, params = build_occurrence_dates_query(filter_type="customer", branch="all")

    assert "FROM QI2010 WITH (NOLOCK)" in sql
    assert "D_E_L_E_T_ = ''" in sql
    assert "QI2_TIPO IN (?)" in sql
    assert "QI2_FILIAL" not in sql
    assert params == ("2",)


def test_occurrence_dates_sql_filters_concrete_branch() -> None:
    sql, params = build_occurrence_dates_query(filter_type="customer", branch="01")

    assert "QI2_FILIAL = ?" in sql
    assert params == ("2", "01")


def test_occurrence_dates_sql_all_types_omits_qi2_tipo() -> None:
    sql, params = build_occurrence_dates_query(filter_type="all", branch=None)

    assert "QI2_TIPO" not in sql
    assert params == ()


def test_occurrence_dates_sql_filters_product_prefix_as_item_starts_with() -> None:
    sql, params = build_occurrence_dates_query(
        filter_type="customer",
        product_prefix="9048",
    )

    assert "QI2_ITEM LIKE ?" in sql
    assert params == ("2", "9048%")
