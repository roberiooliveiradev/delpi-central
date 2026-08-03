"""Testes SQL builder — programas de máquina / top intermediários."""

from __future__ import annotations

from app.domain.services.supplies.safety_stock_stock_projection_service import (
    FINISHED_PRODUCTION_ORDER_SUFFIX,
)
from app.infrastructure.persistence.totvs.production_repositories.production_machine_programs_sql import (
    build_top_intermediates_sql,
)


def test_top_intermediates_sql_joins_pa_sg2_and_open_op() -> None:
    sql_items, sql_count, params = build_top_intermediates_sql(
        branch="01",
        search=None,
        offset=0,
        page_size=50,
    )
    assert "SH6010" in sql_items
    assert "B1_TIPO" in sql_items
    assert "'PI'" in sql_items
    assert "LIKE '5%'" in sql_items
    assert "CT-02A" in sql_items
    assert "NOT IN" in sql_items
    assert FINISHED_PRODUCTION_ORDER_SUFFIX in sql_items
    assert "G2_OPERAC" in sql_items
    assert "'01'" in sql_items  # operação SG2, não filial
    assert "C2_QUANT > OP.C2_QUJE" in sql_items
    assert "OUTER APPLY" in sql_items
    assert "LEFT JOIN SG2010" not in sql_items
    assert "OFFSET 0 ROWS FETCH NEXT 50 ROWS ONLY" in sql_items
    assert "COUNT_BIG(*) AS total" in sql_count
    assert "OFFSET" not in sql_count
    assert "H6_FILIAL = ?" in sql_items
    flat = [p for slot in params for p in slot]
    assert flat.count("01") >= 1


def test_top_intermediates_sql_todas_has_no_branch_predicate() -> None:
    sql_items, _, params = build_top_intermediates_sql(
        branch="Todas",
        search=None,
        offset=0,
        page_size=10,
    )
    assert "H6_FILIAL = ?" not in sql_items
    assert "C2_FILIAL = ?" not in sql_items
    assert "G2_FILIAL = ?" not in sql_items
    assert "01" not in params


def test_top_intermediates_sql_search_filter() -> None:
    sql_items, _, _ = build_top_intermediates_sql(
        branch="02",
        search="%502%",
        offset=50,
        page_size=25,
    )
    assert "LIKE ?" in sql_items
    assert "OFFSET 50 ROWS FETCH NEXT 25 ROWS ONLY" in sql_items
    assert "H6_FILIAL = ?" in sql_items
