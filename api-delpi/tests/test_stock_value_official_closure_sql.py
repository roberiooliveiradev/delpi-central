"""SQL tests for official closure stock value path."""

from app.infrastructure.persistence.totvs.supplies_repositories.stock_value_official_closure_sql import (
    OfficialClosureFilterClauses,
    build_official_closure_params,
    format_official_closure_sql,
)

_EMPTY_FILTERS = OfficialClosureFilterClauses(
    sb9_branch_filter_b9="",
    sb9_location_filter="",
)


def test_official_closure_summary_sql_uses_sb9_period_end() -> None:
    sql = format_official_closure_sql(summary_only=True, filters=_EMPTY_FILTERS)
    assert "B9.B9_DATA = ?" in sql
    assert "closure_items" in sql
    assert "#Delpi_OfficialStockItems" not in sql


def test_official_closure_bundle_sql_materializes_temp_table() -> None:
    sql = format_official_closure_sql(summary_only=False, filters=_EMPTY_FILTERS, top_limit=5)
    assert "#Delpi_OfficialStockItems" in sql
    assert "SELECT TOP 5" in sql


def test_build_official_closure_params_order() -> None:
    params = build_official_closure_params(
        period_end="20260531",
        sb9_b9_params=("01",),
        sb9_loc_params=("A1",),
    )
    assert params == ("20260531", "01", "A1")
