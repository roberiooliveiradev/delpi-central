from unittest.mock import MagicMock, patch

from app.application.dto.supplies.get_stock_value_request import GetStockValueRequest
from app.application.services.supplies.stock_value_cache import stock_value_cache_key
from app.infrastructure.persistence.totvs.supplies_repositories.stock_value_query_repository import (
    StockValueQueryRepository,
)


def test_historical_summary_only_sql_skips_breakdown_selects() -> None:
    repo = StockValueQueryRepository()
    request = GetStockValueRequest(
        start_date="2026-04-01",
        end_date="2026-04-30",
        summary_only=True,
    )

    sql, _params = repo._format_historical_bundle_sql(request)

    assert "GROUP BY branch" not in sql
    assert "SELECT TOP" not in sql
    assert "COUNT(DISTINCT product_code) AS total_products" in sql


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
