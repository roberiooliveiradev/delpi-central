from unittest.mock import patch

from app.application.dto.supplies.get_stock_value_request import GetStockValueRequest
from app.application.services.supplies.stock_value_cache import stock_value_cache_key
from app.infrastructure.persistence.totvs.supplies_repositories.stock_value_historical_sql import (
    HistoricalStockFilterClauses,
    build_historical_stock_params,
    format_historical_stock_sql,
)
from app.infrastructure.persistence.totvs.supplies_repositories.stock_value_query_repository import (
    StockValueQueryRepository,
)

_EMPTY_FILTERS = HistoricalStockFilterClauses(
    sb9_branch_filter="",
    sb9_branch_filter_b9="",
    sb9_location_filter="",
    d3_branch_filter="",
    d3_location_filter="",
)


def test_historical_summary_only_sql_skips_temp_table_and_breakdown() -> None:
    repo = StockValueQueryRepository()
    request = GetStockValueRequest(
        start_date="2026-04-01",
        end_date="2026-04-30",
        summary_only=True,
    )

    sql, _params = repo._format_historical_bundle_sql(request)

    assert "#Delpi_StockItems" not in sql
    assert "DROP TABLE IF EXISTS" not in sql
    assert "GROUP BY branch" not in sql
    assert "SELECT TOP" not in sql
    assert "COUNT(DISTINCT product_code) AS total_products" in sql
    assert sql.count("FROM SD3010") == 1
    assert "movimentos_sd3" in sql
    assert "item_keys" in sql
    assert "FULL OUTER JOIN" not in sql


def test_historical_full_bundle_materializes_once_and_scans_sd3_once() -> None:
    repo = StockValueQueryRepository()
    request = GetStockValueRequest(
        start_date="2026-04-01",
        end_date="2026-04-30",
        summary_only=False,
    )

    sql, _params = repo._format_historical_bundle_sql(request)

    assert "#Delpi_StockItems" in sql
    assert sql.count("FROM SD3010") == 1
    assert "FULL OUTER JOIN" not in sql


def test_historical_params_apply_d3_filters_once() -> None:
    repo = StockValueQueryRepository()
    request = GetStockValueRequest(
        branch="01",
        start_date="2026-04-01",
        end_date="2026-04-30",
        summary_only=True,
    )

    _sql, params = repo._format_historical_bundle_sql(request)

    assert params.count("01") == 3


def test_build_historical_stock_params_matches_cte_placeholder_order() -> None:
    params = build_historical_stock_params(
        period_start="20260401",
        period_end_exclusive="20260501",
        sb9_params=("01",),
        sb9_b9_params=("01",),
        sb9_loc_params=("A1",),
        d3_params=("01",),
        d3_loc_params=("A1",),
    )

    assert params == (
        "20260401",
        "01",
        "01",
        "A1",
        "20260401",
        "20260401",
        "20260401",
        "20260501",
        "20260401",
        "20260501",
        "20260501",
        "01",
        "A1",
    )


def test_movimentos_sd3_uses_single_range_filter() -> None:
    sql = format_historical_stock_sql(summary_only=True, filters=_EMPTY_FILTERS)

    assert "D3.D3_EMISSAO > U.closing_base_date" in sql
    assert "D3.D3_EMISSAO < ?" in sql
    assert " OR " not in sql.split("movimentos_sd3")[1].split("item_keys")[0]


def test_format_historical_stock_sql_reuses_shared_ctes() -> None:
    summary_sql = format_historical_stock_sql(
        summary_only=True,
        filters=_EMPTY_FILTERS,
    )
    bundle_sql = format_historical_stock_sql(
        summary_only=False,
        filters=_EMPTY_FILTERS,
        top_limit=5,
    )

    assert "movimentos_sd3" in summary_sql
    assert "movimentos_sd3" in bundle_sql
    assert "SELECT TOP 5" in bundle_sql
    assert "SELECT TOP" not in summary_sql


def test_current_summary_only_sql_uses_single_select() -> None:
    repo = StockValueQueryRepository()
    request = GetStockValueRequest(summary_only=True)

    with patch.object(
        StockValueQueryRepository,
        "execute_query_multiple",
        return_value=[{"data": [{"total_stock_value": 1.0, "total_stock_quantity": 1.0}]}],
    ) as execute_mock:
        with patch.object(StockValueQueryRepository, "__enter__", return_value=repo):
            with patch.object(StockValueQueryRepository, "__exit__", return_value=False):
                repo._fetch_current_bundle(request)

    sql = execute_mock.call_args[0][0]
    assert sql.count("FROM SB2010 SB2") == 1
    assert "GROUP BY SB2.B2_FILIAL" not in sql


def test_summary_only_uses_distinct_cache_key() -> None:
    full = GetStockValueRequest(start_date="2026-04-01", end_date="2026-04-30")
    lite = GetStockValueRequest(
        start_date="2026-04-01",
        end_date="2026-04-30",
        summary_only=True,
    )

    assert stock_value_cache_key(full) != stock_value_cache_key(lite)


def test_inventory_turnover_stock_request_is_summary_only() -> None:
    from app.application.dto.supplies.get_inventory_turnover_request import (
        GetInventoryTurnoverRequest,
    )
    from app.application.use_cases.supplies.get_inventory_turnover_use_case import (
        GetInventoryTurnoverUseCase,
    )

    stock_request = GetInventoryTurnoverUseCase._to_stock_request(
        GetInventoryTurnoverRequest(
            start_date="2026-04-01",
            end_date="2026-04-30",
        )
    )

    assert stock_request.summary_only is True
