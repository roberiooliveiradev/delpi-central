from app.infrastructure.persistence.totvs.commercial_repositories.sales_order_otd_sql import (
    build_sales_order_otd_filters,
    build_sales_order_otd_sql,
)


def test_build_sales_order_otd_filters_includes_open_lines_without_invoice_requirement() -> None:
    where_clause, _ = build_sales_order_otd_filters(
        branch="02",
        start_date="2026-07-01",
        end_date="2026-07-08",
        customer_segment="weg",
    )

    assert "C6.C6_DATFAT IS NOT NULL" not in where_clause
    assert "C6.C6_QTDENT >= C6.C6_QTDVEN" not in where_clause
    assert "C6.C6_QTDVEN > 0" in where_clause
    assert "C6.C6_ENTREG" in where_clause


def test_build_sales_order_otd_sql_classifies_invoiced_and_open_lines() -> None:
    sql, params = build_sales_order_otd_sql(
        where_clause="1=1",
        reference_end_date="2026-07-08",
    )

    assert "linhas_elegiveis" in sql
    assert "C6_DATFAT <= C6_ENTREG" in sql
    assert "COALESCE(?, CONVERT(VARCHAR(8), GETDATE(), 112)) > C6_ENTREG" in sql
    assert params == ("20260708", "20260708", "20260708")
