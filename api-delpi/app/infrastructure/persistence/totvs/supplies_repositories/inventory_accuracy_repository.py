"""Repository — acuracidade do inventário físico (SB7 × SD3 INVENT)."""

from __future__ import annotations

from typing import Any, Sequence

from app.domain.ports.supplies.inventory_accuracy_repository_port import (
    InventoryAccuracyRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.supplies_repositories import (
    inventory_accuracy_sql as sql,
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


class InventoryAccuracyRepository(BaseRepository, InventoryAccuracyRepositoryPort):
    def fetch_last_closing_date(
        self, *, branches: Sequence[str]
    ) -> str | None:
        query, params = sql.build_last_closing_query(branches)
        with self as repo:
            row = repo.execute_one(query, tuple(params))
        closing = str((row or {}).get("last_closing") or "").strip()
        return closing or None

    def fetch_summary(
        self,
        *,
        branches: Sequence[str],
        period_start: str,
        period_end_exclusive: str,
    ) -> dict[str, Any]:
        query, params = sql.build_summary_queries(
            branches=branches,
            period_start=period_start,
            period_end_exclusive=period_end_exclusive,
        )
        with self as repo:
            resultsets = repo.execute_query_multiple(query, tuple(params))
        datasets = [item.get("data") or [] for item in resultsets]
        totals = datasets[0][0] if datasets and datasets[0] else {}
        by_branch = datasets[1] if len(datasets) > 1 else []
        return {
            "totals": {
                "valid_count_total": _i(totals.get("valid_count_total")),
                "evaluable_count_total": _i(
                    totals.get("evaluable_count_total")
                ),
                "accurate_count": _i(totals.get("accurate_count")),
                "divergent_count": _i(totals.get("divergent_count")),
                "excluded_count": _i(totals.get("excluded_count")),
                "excluded_pending_processing": _i(
                    totals.get("excluded_pending_processing")
                ),
                "shortage_value_total": _f(
                    totals.get("shortage_value_total")
                ),
                "surplus_value_total": _f(
                    totals.get("surplus_value_total")
                ),
            },
            "by_branch": [
                {
                    "branch": str(row.get("branch") or "").strip(),
                    "valid_count_total": _i(row.get("valid_count_total")),
                    "evaluable_count_total": _i(
                        row.get("evaluable_count_total")
                    ),
                    "accurate_count": _i(row.get("accurate_count")),
                    "divergent_count": _i(row.get("divergent_count")),
                    "excluded_count": _i(row.get("excluded_count")),
                    "shortage_value_total": _f(
                        row.get("shortage_value_total")
                    ),
                    "surplus_value_total": _f(
                        row.get("surplus_value_total")
                    ),
                }
                for row in by_branch
            ],
        }

    def count_cancelled_events(
        self,
        *,
        branches: Sequence[str],
        period_start: str,
        period_end_exclusive: str,
    ) -> int:
        query, params = sql.build_cancelled_count_query(
            branches=branches,
            period_start=period_start,
            period_end_exclusive=period_end_exclusive,
        )
        with self as repo:
            row = repo.execute_one(query, tuple(params))
        return _i((row or {}).get("cancelled_count"))

    def count_items(
        self,
        *,
        branches: Sequence[str],
        period_start: str,
        period_end_exclusive: str,
        outcome: str | None = None,
    ) -> int:
        query, params = sql.build_count_query(
            branches=branches,
            period_start=period_start,
            period_end_exclusive=period_end_exclusive,
            outcome=outcome,
        )
        with self as repo:
            row = repo.execute_one(query, tuple(params))
        return _i((row or {}).get("total"))

    def fetch_items(
        self,
        *,
        branches: Sequence[str],
        period_start: str,
        period_end_exclusive: str,
        outcome: str | None = None,
        sort: str,
        offset: int,
        page_size: int,
    ) -> list[dict[str, Any]]:
        query, params = sql.build_items_query(
            branches=branches,
            period_start=period_start,
            period_end_exclusive=period_end_exclusive,
            outcome=outcome,
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
                "blocked": bool(_i(row.get("blocked"))),
                "warehouse": str(row.get("warehouse") or "").strip(),
                "count_date": _iso_date(row.get("count_date")),
                "counted_quantity": _f(row.get("counted_quantity")),
                "theoretical_quantity": _f(row.get("theoretical_quantity")),
                "divergence_quantity": _f(row.get("theoretical_quantity"))
                - _f(row.get("counted_quantity")),
                "shortage_quantity": _f(row.get("shortage_quantity")),
                "surplus_quantity": _f(row.get("surplus_quantity")),
                "shortage_value": _f(row.get("shortage_value")),
                "surplus_value": _f(row.get("surplus_value")),
                "adjustment_rows": _i(row.get("adjustment_rows")),
                "physical_lines": _i(row.get("physical_lines")),
                "inventory_document": (
                    str(row.get("inventory_document") or "").strip() or None
                ),
                "count_status": str(row.get("count_status") or "").strip(),
                "outcome": str(row.get("outcome") or "").strip(),
                "exclusion_reason": (
                    str(row.get("exclusion_reason") or "").strip() or None
                ),
            }
            for row in rows
        ]
