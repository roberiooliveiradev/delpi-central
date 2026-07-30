"""Repository — saldos de estoque por armazém (SB2)."""

from __future__ import annotations

from typing import Any

from app.domain.ports.supplies.stock_balances_query_repository_port import (
    StockBalancesQueryRepositoryPort,
)
from app.domain.totvs.protheus_warehouses import WAREHOUSE_LABELS_PT
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.supplies_repositories import stock_balances_sql as sql


def _f(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _i(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


class StockBalancesQueryRepository(BaseRepository, StockBalancesQueryRepositoryPort):
    def fetch_summary(
        self,
        *,
        branch: str | None,
        warehouse: str | None,
        only_positive: bool,
    ) -> dict[str, Any]:
        where_clause, params = sql.build_where_clause(
            branch=branch,
            warehouse=warehouse,
            only_positive=only_positive,
        )
        summary_sql = sql.format_summary_sql(where_clause)
        by_wh_sql = sql.format_by_warehouse_sql(where_clause)
        combined = f"{summary_sql};\n\n{by_wh_sql}"
        param_tuple = tuple(params + params)

        with self as repo:
            resultsets = repo.execute_query_multiple(combined, param_tuple)

        summary_rows = resultsets[0] if resultsets else []
        by_rows = resultsets[1] if len(resultsets) > 1 else []
        summary_row = summary_rows[0] if summary_rows else {}

        by_warehouse = [
            {
                "branch": str(row.get("branch") or "").strip(),
                "warehouse": str(row.get("warehouse") or "").strip(),
                "warehouse_label": WAREHOUSE_LABELS_PT.get(
                    str(row.get("warehouse") or "").strip(),
                    None,
                ),
                "product_count": _i(row.get("product_count")),
                "total_quantity": _f(row.get("total_quantity")),
                "total_stock_value": _f(row.get("total_stock_value")),
                "total_stock_value_vatu1": _f(row.get("total_stock_value_vatu1")),
            }
            for row in by_rows
        ]

        return {
            "summary": {
                "branch": branch or "consolidated",
                "warehouse": warehouse or "all",
                "product_count": _i(summary_row.get("product_count")),
                "total_quantity": _f(summary_row.get("total_quantity")),
                "total_stock_value": _f(summary_row.get("total_stock_value")),
                "total_stock_value_vatu1": _f(
                    summary_row.get("total_stock_value_vatu1")
                ),
                "warehouse_count": _i(summary_row.get("warehouse_count")),
                "valuation": "qatu_times_cm1_same_local",
            },
            "by_warehouse": by_warehouse,
        }

    def count_items(
        self,
        *,
        branch: str | None,
        warehouse: str | None,
        only_positive: bool,
    ) -> int:
        where_clause, params = sql.build_where_clause(
            branch=branch,
            warehouse=warehouse,
            only_positive=only_positive,
        )
        query = sql.format_count_items_sql(where_clause)
        with self as repo:
            rows = repo.execute_query(query, tuple(params))
        return _i((rows[0] if rows else {}).get("total"))

    def fetch_items(
        self,
        *,
        branch: str | None,
        warehouse: str | None,
        only_positive: bool,
        sort: str,
        offset: int,
        page_size: int,
    ) -> list[dict[str, Any]]:
        where_clause, params = sql.build_where_clause(
            branch=branch,
            warehouse=warehouse,
            only_positive=only_positive,
        )
        order_by = sql.resolve_order_by(sort)
        query = sql.format_items_sql(where_clause, order_by=order_by)
        query_params = tuple(params) + (offset, page_size)

        with self as repo:
            rows = repo.execute_query(query, query_params)

        return [
            {
                "product_code": str(row.get("product_code") or "").strip(),
                "description": str(row.get("description") or "").strip(),
                "branch": str(row.get("branch") or "").strip(),
                "warehouse": str(row.get("warehouse") or "").strip(),
                "warehouse_label": WAREHOUSE_LABELS_PT.get(
                    str(row.get("warehouse") or "").strip(),
                    None,
                ),
                "quantity": _f(row.get("quantity")),
                "unit_cost": _f(row.get("unit_cost")),
                "stock_value": _f(row.get("stock_value")),
            }
            for row in rows
        ]
