"""Read-only GLPI #635: confirmed SC release to first linked purchase order."""

from __future__ import annotations

from math import ceil
from typing import Any

from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_sc_pc_conversion_sql import (
    PAGE_SIZE, MAX_PAGE_SIZE, build_conversion_cohort,
    build_conversion_batch_sql, build_conversion_summary_sql,
)


def _summary(row: dict[str, Any] | None) -> dict[str, Any]:
    row = row or {}
    keys = (
        "approved_requests", "with_approval", "without_approval",
        "converted_requests", "pending_requests", "future_pending_requests",
        "measured_requests", "before_release", "invalid_order_dates",
        "sum_conversion_days", "sum_pending_days", "sum_measured_days",
        "same_day", "one_to_two_days", "three_to_five_days",
        "six_to_ten_days", "over_ten_days",
    )
    result = {key: int(row.get(key) or 0) for key in keys}
    for key in ("avg_days", "avg_completed_days", "avg_pending_days"):
        result[key] = (
            float(row[key]) if row.get(key) not in (None, "") else None
        )
    return result


class PurchaseRequestScPcConversionRepository(BaseRepository):
    def get_conversion(
        self, *,
        branches: list[str] | None,
        date_from: str | None = None,
        date_to: str | None = None,
        request_number: str | None = None,
        page: int = 1,
        page_size: int = PAGE_SIZE,
        summary_only: bool = False,
    ) -> dict[str, Any]:
        if not 1 <= page <= 100000 or not 1 <= page_size <= MAX_PAGE_SIZE:
            raise ValueError("Paginação inválida.")
        cohort, params, filters = build_conversion_cohort(
            branches=branches, date_from=date_from,
            date_to=date_to, request_number=request_number,
        )
        with self as repo:
            if summary_only:
                # Strategic Indicators never needs a page; stay pure SELECT.
                summaries = repo.execute_query(
                    build_conversion_summary_sql(cohort), tuple(params),
                )
                records = []
            else:
                # Prevent two full SC/SCR/SC7 scans per browser request.
                # execute_query_multiple already handles NOCOUNT and multiple
                # resultsets on the same SQL Server connection.
                datasets = repo.execute_query_multiple(
                    build_conversion_batch_sql(cohort),
                    tuple(params) + ((page - 1) * page_size, page_size),
                )
                if len(datasets) != 2:
                    raise RuntimeError(
                        "Unexpected SC/PC conversion SQL result-set count"
                    )
                summaries = datasets[0]["data"]
                records = datasets[1]["data"]

        consolidated = next(
            (row for row in summaries if row.get("branch") in (None, "")), None,
        )
        by_branch = {
            str(row["branch"]).strip(): _summary(row)
            for row in summaries if row.get("branch") not in (None, "")
        }
        summary = _summary(consolidated)
        items = [
            {
                "branch": str(row.get("branch") or "").strip(),
                "request_number": str(row.get("request_number") or "").strip(),
                "issue_date": row.get("issue_date") or None,
                "final_approval_date": row.get("final_approval_date") or None,
                "effective_start_date": row.get("effective_start_date") or None,
                "start_date_source": row.get("start_date_source"),
                "first_order_date": row.get("first_order_date") or None,
                "first_order_number": row.get("first_order_number") or None,
                "linked_order_count": int(row.get("linked_order_count") or 0),
                "approval_levels": int(row.get("approval_levels") or 0),
                "item_count": int(row.get("item_count") or 0),
                "conversion_status": row.get("conversion_status"),
                "conversion_days": (
                    int(row["conversion_days"])
                    if row.get("conversion_days") not in (None, "") else None
                ),
                "pending_age_days": (
                    int(row["pending_age_days"])
                    if row.get("pending_age_days") not in (None, "") else None
                ),
            }
            for row in records
        ]
        return {
            "source": "SC1010+SCR010+SC7010",
            "scope": "release_or_issue_without_approval_to_first_order",
            "unit": "calendar_days",
            "period_anchor": "effective_start_date",
            "as_of_date": filters["as_of_date"],
            "calculation_mode": "completed_or_pending_elapsed_as_of_today",
            "filters": filters,
            "summary": summary,
            "branch_breakdown": by_branch,
            "items": items,
            "total": summary["approved_requests"],
            "page": page,
            "page_size": page_size,
            "total_pages": (
                ceil(summary["approved_requests"] / page_size)
                if not summary_only else 0
            ),
        }
