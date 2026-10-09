"""Repository — matérias-primas sem giro (SB2 × SD3 × SB9)."""

from __future__ import annotations

from typing import Any, Sequence

from app.domain.ports.supplies.non_moving_stock_repository_port import (
    NonMovingStockRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.supplies_repositories import (
    non_moving_stock_sql as sql,
)


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


def _iso_date(yyyymmdd: Any) -> str | None:
    text = str(yyyymmdd or "").strip()
    if len(text) != 8 or not text.isdigit():
        return None
    return f"{text[:4]}-{text[4:6]}-{text[6:8]}"


class NonMovingStockQueryRepository(BaseRepository, NonMovingStockRepositoryPort):
    def fetch_summary(
        self,
        *,
        branches: Sequence[str],
        warehouses: Sequence[str],
        window_start: str,
        window_end: str,
        no_consumption_status: str,
    ) -> dict[str, Any]:
        query, params = sql.build_summary_queries(
            branches=branches,
            warehouses=warehouses,
            window_start=window_start,
            window_end=window_end,
            no_consumption_status=no_consumption_status,
        )
        with self as repo:
            resultsets = repo.execute_query_multiple(query, tuple(params))
        datasets = [item.get("data") or [] for item in resultsets]
        totals = datasets[0][0] if datasets and datasets[0] else {}
        by_status = datasets[1] if len(datasets) > 1 else []
        by_branch = datasets[2] if len(datasets) > 2 else []
        return {
            "totals": {
                "row_count": _i(totals.get("row_count")),
                "product_count": _i(totals.get("product_count")),
                "eligible_stock_value": _f(totals.get("eligible_stock_value")),
                "insufficient_history_stock_value": _f(
                    totals.get("insufficient_history_stock_value")
                ),
                "no_consumption_stock_value": _f(
                    totals.get("no_consumption_stock_value")
                ),
                "with_consumption_stock_value": _f(
                    totals.get("with_consumption_stock_value")
                ),
                "blocked_stock_value": _f(totals.get("blocked_stock_value")),
                "blocked_no_consumption_stock_value": _f(
                    totals.get("blocked_no_consumption_stock_value")
                ),
                "blocked_product_count": _i(
                    totals.get("blocked_product_count")
                ),
                "zero_cost_item_count": _i(
                    totals.get("zero_cost_item_count")
                ),
                "with_consumption_count": _i(
                    totals.get("with_consumption_count")
                ),
                "no_consumption_count": _i(totals.get("no_consumption_count")),
                "insufficient_history_count": _i(
                    totals.get("insufficient_history_count")
                ),
            },
            "by_status": [
                {
                    "turnover_status": str(
                        row.get("turnover_status") or ""
                    ).strip(),
                    "product_count": _i(row.get("product_count")),
                    "stock_value": _f(row.get("stock_value")),
                    "blocked_stock_value": _f(
                        row.get("blocked_stock_value")
                    ),
                }
                for row in by_status
            ],
            "by_branch": [
                {
                    "branch": str(row.get("branch") or "").strip(),
                    "product_count": _i(row.get("product_count")),
                    "eligible_stock_value": _f(
                        row.get("eligible_stock_value")
                    ),
                    "no_consumption_stock_value": _f(
                        row.get("no_consumption_stock_value")
                    ),
                    "insufficient_history_stock_value": _f(
                        row.get("insufficient_history_stock_value")
                    ),
                    "blocked_stock_value": _f(
                        row.get("blocked_stock_value")
                    ),
                }
                for row in by_branch
            ],
        }

    def count_items(
        self,
        *,
        branches: Sequence[str],
        warehouses: Sequence[str],
        window_start: str,
        window_end: str,
        no_consumption_status: str,
        product_codes: Sequence[str] | None = None,
        turnover_status: str | None = None,
        blocked: bool | None = None,
        search: str | None = None,
    ) -> int:
        query, params = sql.build_count_query(
            branches=branches,
            warehouses=warehouses,
            window_start=window_start,
            window_end=window_end,
            no_consumption_status=no_consumption_status,
            product_codes=product_codes,
            turnover_status=turnover_status,
            blocked=blocked,
            search=search,
        )
        with self as repo:
            row = repo.execute_one(query, tuple(params))
        return _i((row or {}).get("total"))

    def fetch_items(
        self,
        *,
        branches: Sequence[str],
        warehouses: Sequence[str],
        window_start: str,
        window_end: str,
        no_consumption_status: str,
        product_codes: Sequence[str] | None = None,
        turnover_status: str | None = None,
        blocked: bool | None = None,
        search: str | None = None,
        sort: str,
        offset: int,
        page_size: int,
    ) -> list[dict[str, Any]]:
        query, params = sql.build_items_query(
            branches=branches,
            warehouses=warehouses,
            window_start=window_start,
            window_end=window_end,
            no_consumption_status=no_consumption_status,
            product_codes=product_codes,
            turnover_status=turnover_status,
            blocked=blocked,
            search=search,
            sort=sort,
            offset=offset,
            page_size=page_size,
        )
        with self as repo:
            rows = repo.execute_query(query, tuple(params))
        return [
            {
                "branch": str(row.get("branch") or "").strip(),
                "product_code": str(row.get("product_code") or "").strip(),
                "description": str(row.get("description") or "").strip()
                or None,
                "unit_of_measure": str(
                    row.get("unit_of_measure") or ""
                ).strip()
                or None,
                "warehouse": str(row.get("warehouse") or "").strip(),
                "quantity": _f(row.get("quantity")),
                "unit_cost": _f(row.get("unit_cost")),
                "stock_value": _f(row.get("stock_value")),
                "blocked": bool(_i(row.get("blocked"))),
                "turnover_status": str(
                    row.get("turnover_status") or ""
                ).strip(),
                "last_effective_utilization": _iso_date(
                    row.get("last_effective_utilization")
                ),
                "last_utilization_in_window": _iso_date(
                    row.get("last_util_in_window")
                ),
            }
            for row in rows
        ]
