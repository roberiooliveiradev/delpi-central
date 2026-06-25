from unittest.mock import patch

from app.application.dto.supplies.get_stock_value_request import GetStockValueRequest
from app.application.services.supplies.stock_value_cache import stock_value_cache_key
from app.infrastructure.persistence.totvs.supplies_repositories.stock_value_historical_sql import (
    HistoricalStockFilterClauses,
    build_historical_method_breakdown_params,
    build_historical_method_routing_params,
    build_historical_stock_params,
    format_historical_breakdown_sql,
    format_historical_method_breakdown_sql,
    format_historical_stock_sql,
)
from app.infrastructure.persistence.totvs.supplies_repositories.stock_value_query_repository import (
    StockValueQueryRepository,
)

_EMPTY_FILTERS = HistoricalStockFilterClauses(
    sb9_branch_filter="",
    sb9_branch_filter_b9="",
    sb9_branch_filter_official="",
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
    assert "GROUP BY branch\n        ORDER BY branch" not in sql
    assert "SELECT TOP" not in sql
    assert "COUNT(DISTINCT product_code) AS total_products" in sql
    assert sql.count("FROM SD3010") == 1
    assert "movimentos_sd3" in sql
    assert "item_totals" in sql
    assert "estoque_item" not in sql
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


def test_historical_summary_only_sql_skips_breakdown_ctes() -> None:
    repo = StockValueQueryRepository()
    request = GetStockValueRequest(
        start_date="2026-04-01",
        end_date="2026-04-30",
        summary_only=True,
    )

    sql, _params = repo._format_historical_bundle_sql(request)

    assert "branch_breakdown" not in sql
    assert "FROM item_totals" in sql

    breakdown_sql = format_historical_breakdown_sql(filters=_EMPTY_FILTERS)
    assert "branch_breakdown" in breakdown_sql
    assert "official_closure_on_period_end" in breakdown_sql


def test_build_historical_stock_params_matches_cte_placeholder_order() -> None:
    params = build_historical_stock_params(
        period_start="20260401",
        period_end="20260430",
        period_end_exclusive="20260501",
        sb9_params=("01",),
        sb9_b9_params=("01",),
        sb9_official_params=("01",),
        sb9_loc_params=("A1",),
        d3_params=("01",),
        d3_loc_params=("A1",),
        include_breakdown_select=False,
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


def test_build_historical_breakdown_params_include_period_end() -> None:
    params = build_historical_stock_params(
        period_start="20260401",
        period_end="20260430",
        period_end_exclusive="20260501",
        sb9_params=("01",),
        sb9_b9_params=("01",),
        sb9_official_params=("01",),
        sb9_loc_params=(),
        d3_params=("01",),
        d3_loc_params=(),
        include_breakdown_select=True,
    )

    assert params[-1] == "20260430"
    assert params[-3] == "20260430"
    assert params.count("01") == 4


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


def test_current_full_bundle_repeats_filter_params_per_select() -> None:
    repo = StockValueQueryRepository()
    request = GetStockValueRequest(branch="01", top_limit=5, summary_only=False)

    with patch.object(
        StockValueQueryRepository,
        "execute_query_multiple",
        return_value=[
            {"data": [{"total_stock_value": 1.0, "total_stock_quantity": 1.0}]},
            {"data": []},
            {"data": []},
            {"data": []},
        ],
    ) as execute_mock:
        with patch.object(StockValueQueryRepository, "__enter__", return_value=repo):
            with patch.object(StockValueQueryRepository, "__exit__", return_value=False):
                repo._fetch_current_bundle(request)

    sql, params = execute_mock.call_args[0]
    marker_count = sql.count("?")
    assert marker_count == len(params)
    assert params == ("01", "all", "01", "01", "01", "01")


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


def test_consolidated_summary_only_fans_out_per_branch() -> None:
    repo = StockValueQueryRepository()
    request = GetStockValueRequest(
        start_date="2026-04-01",
        end_date="2026-04-30",
        summary_only=True,
    )

    branch_calls: list[str] = []

    def fake_branch_bundle(
        branch_request: GetStockValueRequest,
        *,
        shared_breakdown_rows=None,
    ) -> dict:
        branch_calls.append(branch_request.branch or "")
        return {
            "summary": {
                "branch": branch_request.branch,
                "location": "all",
                "total_stock_value": 100.0,
                "total_stock_quantity": 10.0,
                "total_records": 1,
                "total_products": 1,
                "total_locations": 1,
            },
            "by_branch": [],
            "by_location": [],
            "top_products": [],
        }

    with patch.object(
        StockValueQueryRepository,
        "_fetch_branch_bundle",
        side_effect=fake_branch_bundle,
    ):
        bundle = repo._fetch_consolidated_bundle(request)

    assert branch_calls == ["01", "02"]
    assert bundle["summary"]["total_stock_value"] == 200.0
    assert len(bundle["by_branch"]) == 2


def test_historical_method_breakdown_sql_skips_sd3() -> None:
    sql = format_historical_method_breakdown_sql(filters=_EMPTY_FILTERS)

    assert "FROM SD3010" not in sql
    assert "movimentos_sd3" not in sql
    assert "branch_dates AS" in sql
    assert "branch_values AS" in sql
    assert "OVER (PARTITION BY" not in sql
    assert sql.count("FROM SB9010") == 2
    assert "official_closure_on_period_end" in sql


def test_historical_method_routing_sql_single_sb9_scan() -> None:
    sql = format_historical_method_breakdown_sql(
        filters=_EMPTY_FILTERS,
        routing_only=True,
    )

    assert sql.count("FROM SB9010") == 1
    assert "branch_values" not in sql
    assert "B9.B9_DATA <=" in sql


def test_build_historical_method_breakdown_params_matches_placeholders() -> None:
    params = build_historical_method_breakdown_params(
        period_start="20260601",
        period_end="20260624",
        sb9_params=("02",),
        sb9_b9_params=("02",),
        sb9_loc_params=(),
    )

    sql = format_historical_method_breakdown_sql(
        filters=HistoricalStockFilterClauses(
            sb9_branch_filter=" AND B9_FILIAL = ?",
            sb9_branch_filter_b9=" AND B9.B9_FILIAL = ?",
            sb9_branch_filter_official=" AND B9.B9_FILIAL = ?",
            sb9_location_filter="",
            d3_branch_filter="",
            d3_location_filter="",
        )
    )
    assert sql.count("?") == len(params)
    assert params == (
        "20260601",
        "20260624",
        "20260624",
        "02",
        "02",
        "20260624",
    )


def test_build_historical_method_routing_params_matches_placeholders() -> None:
    params = build_historical_method_routing_params(
        period_start="20260601",
        period_end="20260624",
        sb9_params=("02",),
    )
    sql = format_historical_method_breakdown_sql(
        filters=HistoricalStockFilterClauses(
            sb9_branch_filter=" AND B9_FILIAL = ?",
            sb9_branch_filter_b9="",
            sb9_branch_filter_official="",
            sb9_location_filter="",
            d3_branch_filter="",
            d3_location_filter="",
        ),
        routing_only=True,
    )
    assert sql.count("?") == len(params)
    assert params == (
        "20260601",
        "20260624",
        "20260624",
        "20260624",
        "20260624",
        "20260624",
        "20260624",
        "02",
    )


def test_fetch_historical_breakdown_uses_routing_for_auto_hybrid() -> None:
    repo = StockValueQueryRepository()
    request = GetStockValueRequest(
        start_date="2026-06-01",
        end_date="2026-06-24",
        summary_only=False,
        stock_method="auto",
    )

    with patch.object(
        StockValueQueryRepository,
        "_format_historical_method_breakdown_sql",
        return_value=("SELECT 1", ()),
    ) as format_mock:
        with patch.object(StockValueQueryRepository, "__enter__", return_value=repo):
            with patch.object(StockValueQueryRepository, "__exit__", return_value=False):
                with patch.object(
                    StockValueQueryRepository,
                    "execute_query",
                    return_value=[],
                ):
                    repo._fetch_historical_breakdown_rows(request, full_kardex=False)

    format_mock.assert_called_once()
    sql = format_mock.return_value[0]
    assert sql == "SELECT 1"


def test_enrich_closing_values_sql_uses_values_join() -> None:
    from app.infrastructure.persistence.totvs.supplies_repositories.stock_value_historical_sql import (
        build_enrich_closing_values_params,
        format_enrich_closing_values_sql,
    )

    pairs = [("01", "20260228"), ("02", "20260228")]
    sql = format_enrich_closing_values_sql(pairs)
    params = build_enrich_closing_values_params(pairs)

    assert "VALUES (?, ?), (?, ?)" in sql
    assert sql.count("FROM SB9010") == 1
    assert "branch_dates AS" not in sql
    assert params == ("01", "20260228", "02", "20260228")


def test_enrich_breakdown_closing_values_merges_sb9_totals() -> None:
    repo = StockValueQueryRepository()
    rows = [
        {
            "branch": "01",
            "closing_base_date": "20260228",
            "closing_base_value": 0.0,
        },
        {
            "branch": "02",
            "closing_base_date": "20260228",
            "closing_base_value": 0.0,
        },
    ]

    with patch.object(StockValueQueryRepository, "__enter__", return_value=repo):
        with patch.object(StockValueQueryRepository, "__exit__", return_value=False):
            with patch.object(
                StockValueQueryRepository,
                "execute_query",
                return_value=[
                    {"branch": "01", "closing_base_value": 100.0},
                    {"branch": "02", "closing_base_value": 200.0},
                ],
            ):
                enriched = repo._enrich_breakdown_closing_values(
                    rows,
                    branches=("01", "02"),
                )

    assert enriched[0]["closing_base_value"] == 100.0
    assert enriched[1]["closing_base_value"] == 200.0


def test_fetch_historical_bundle_uses_light_breakdown_for_auto() -> None:
    repo = StockValueQueryRepository()

    with patch.object(
        StockValueQueryRepository,
        "_fetch_historical_breakdown_rows",
    ) as breakdown_mock:
        with patch.object(
            StockValueQueryRepository,
            "_fetch_register_snapshot_bundle",
            return_value={"summary": {}, "by_branch": [], "by_location": [], "top_products": []},
        ) as register_mock:
            breakdown_mock.return_value = [
                {
                    "branch": "02",
                    "closing_base_date": "20260228",
                    "closing_base_value": 1.0,
                    "bridge_value": 0.0,
                    "period_net_value": 0.0,
                    "official_closure_date": None,
                    "official_closure_value": None,
                    "official_closure_available": False,
                    "official_closure_on_period_end": False,
                }
            ]
            repo._fetch_historical_bundle(
                GetStockValueRequest(
                    branch="02",
                    start_date="2026-06-01",
                    end_date="2026-06-24",
                    stock_method="auto",
                )
            )

    breakdown_mock.assert_called_once()
    assert breakdown_mock.call_args.kwargs.get("full_kardex") is False
    register_mock.assert_called_once()


def test_consolidated_historical_auto_prefetches_breakdown_once() -> None:
    repo = StockValueQueryRepository()
    request = GetStockValueRequest(
        start_date="2026-06-01",
        end_date="2026-06-24",
        stock_method="auto",
        summary_only=True,
    )
    breakdown_rows = [
        {
            "branch": "01",
            "closing_base_date": "20260228",
            "closing_base_value": 1.0,
            "bridge_value": 0.0,
            "period_net_value": 0.0,
            "official_closure_date": None,
            "official_closure_value": None,
            "official_closure_available": False,
            "official_closure_on_period_end": False,
        },
        {
            "branch": "02",
            "closing_base_date": "20260228",
            "closing_base_value": 2.0,
            "bridge_value": 0.0,
            "period_net_value": 0.0,
            "official_closure_date": None,
            "official_closure_value": None,
            "official_closure_available": False,
            "official_closure_on_period_end": False,
        },
    ]

    with patch.object(
        StockValueQueryRepository,
        "_fetch_historical_breakdown_rows",
        return_value=breakdown_rows,
    ) as breakdown_mock:
        with patch.object(
            StockValueQueryRepository,
            "_fetch_register_snapshot_bundle",
            side_effect=lambda req, **kwargs: {
                "summary": {
                    "branch": req.branch,
                    "location": "all",
                    "total_stock_value": 100.0,
                    "total_stock_quantity": 1.0,
                    "total_records": 1,
                    "total_products": 1,
                    "total_locations": 1,
                },
                "by_branch": [],
                "by_location": [],
                "top_products": [],
            },
        ):
            repo._fetch_consolidated_bundle(request)

    breakdown_mock.assert_called_once()
    assert breakdown_mock.call_args.kwargs.get("full_kardex") is False


def test_get_stock_value_bundle_uses_fan_out_for_consolidated_historical() -> None:
    repo = StockValueQueryRepository()
    request = GetStockValueRequest(
        start_date="2026-04-01",
        end_date="2026-04-30",
    )
    expected = {
        "summary": {"branch": "consolidated", "total_stock_value": 1.0},
        "by_branch": [],
        "by_location": [],
        "top_products": [],
    }

    with patch.object(
        StockValueQueryRepository,
        "_fetch_consolidated_bundle",
        return_value=expected,
    ) as fan_out_mock:
        with patch.object(
            StockValueQueryRepository,
            "_fetch_historical_bundle",
        ) as historical_mock:
            result = repo.get_stock_value_bundle(request)

    assert result == expected
    fan_out_mock.assert_called_once_with(request)
    historical_mock.assert_not_called()
