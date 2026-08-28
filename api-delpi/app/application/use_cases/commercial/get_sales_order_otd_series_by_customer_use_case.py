"""Use case — OTD flat cliente × período (série por cliente)."""

from __future__ import annotations

from typing import Any, Optional

from app.application.dto.commercial.get_sales_order_otd_series_by_customer_request import (
    GetSalesOrderOtdSeriesByCustomerRequest,
)
from app.application.dto.commercial.sales_order_otd_request import SalesOrderOtdRequest
from app.application.services.charts.chart_series_cache_keys import (
    commercial_sales_order_otd_series_by_customer_cache_key,
)
from app.application.services.production.production_kpi_cache import (
    get_cached_chart_series,
    set_cached_chart_series,
)
from app.application.shared.chart_period_buckets import build_period_buckets
from app.infrastructure.persistence.totvs.commercial_repositories.sales_order_otd_repository import (
    SalesOrderOtdRepository,
)


def _to_iso_date(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    raw = str(value).strip()
    if len(raw) == 8 and raw.isdigit():
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
    return raw


class GetSalesOrderOtdSeriesByCustomerUseCase:
    def __init__(self, *, sales_order_otd_repository: SalesOrderOtdRepository) -> None:
        self._repository = sales_order_otd_repository

    def execute(self, request: GetSalesOrderOtdSeriesByCustomerRequest) -> dict[str, Any]:
        request.validate()

        cache_key = commercial_sales_order_otd_series_by_customer_cache_key(request)
        cached = get_cached_chart_series(cache_key)
        if cached is not None and isinstance(cached, dict) and "all_items" in cached:
            return self._paginate(cached, request.page, request.page_size)

        start_iso = _to_iso_date(request.date_start)
        end_iso = _to_iso_date(request.date_end)

        buckets_result = build_period_buckets(
            start_date=start_iso,
            end_date=end_iso,
            granularity=request.granularity,
        )

        customer_codes, customer_names = self._resolve_customer_scope(
            request=request,
            start_iso=start_iso,
            end_iso=end_iso,
        )
        # Top-N without matches: avoid unfiltered SQL (empty codes = no filter in TOTVS).
        skip_buckets = (
            not request.has_explicit_customer_filter() and customer_codes == []
        )

        all_items: list[dict[str, Any]] = []
        if not skip_buckets:
            for bucket in buckets_result.buckets:
                rows = self._repository.list_sales_order_otd_analysis_by_customer(
                    SalesOrderOtdRequest(
                        branch=request.branch,
                        start_date=bucket.start_date,
                        end_date=bucket.end_date,
                        customer_segment=request.customer_segment,
                        customer_codes=customer_codes,
                        customer_names=customer_names,
                        exclude_customer_codes=request.exclude_customer_codes,
                        exclude_customer_names=request.exclude_customer_names,
                    )
                )
                if customer_codes:
                    code_set = {str(c).strip() for c in customer_codes}
                    rows = [
                        row
                        for row in rows
                        if str(row.get("customer_code") or "").strip() in code_set
                    ]
                for row in rows:
                    all_items.append(
                        {
                            "customer_code": row.get("customer_code"),
                            "customer_store": row.get("customer_store"),
                            "customer_name": row.get("customer_name"),
                            "branch": row.get("branch"),
                            "periodo": bucket.label,
                            "sort_key": bucket.key,
                            "start_date": bucket.start_date,
                            "end_date": bucket.end_date,
                            "total_lines": row.get("total_lines"),
                            "total_qty": row.get("total_qty"),
                            "fulfilled_qty": row.get("fulfilled_qty"),
                            "on_time_lines": row.get("on_time_lines"),
                            "late_lines": row.get("late_lines"),
                            "fulfillment_pct": row.get("fulfillment_pct"),
                            "otd_pct": row.get("otd_pct"),
                            "unit": row.get("unit"),
                            "mixed_units": bool(row.get("mixed_units")),
                        }
                    )

        all_items.sort(
            key=lambda item: (
                str(item.get("sort_key") or ""),
                -(float(item.get("total_qty") or 0)),
                str(item.get("customer_code") or ""),
            )
        )

        customers_count = len(
            {
                (
                    str(item.get("customer_code") or ""),
                    str(item.get("customer_store") or ""),
                )
                for item in all_items
            }
        )

        payload = {
            "start_date": start_iso or request.date_start,
            "end_date": end_iso or request.date_end,
            "branch": request.branch,
            "granularity": request.granularity,
            "truncated": buckets_result.truncated,
            "all_items": all_items,
            "summary_base": {
                "granularity": request.granularity,
                "truncated": buckets_result.truncated,
                "customers_count": customers_count,
                "buckets_count": len(buckets_result.buckets),
            },
        }
        set_cached_chart_series(cache_key, payload)
        return self._paginate(payload, request.page, request.page_size)

    def _resolve_customer_scope(
        self,
        *,
        request: GetSalesOrderOtdSeriesByCustomerRequest,
        start_iso: Optional[str],
        end_iso: Optional[str],
    ) -> tuple[Optional[list[str]], Optional[list[str]]]:
        if request.customer_codes:
            return list(request.customer_codes), request.customer_names
        if request.customer_names:
            return None, list(request.customer_names)

        ranking = self._repository.list_sales_order_otd_analysis_by_customer(
            SalesOrderOtdRequest(
                branch=request.branch,
                start_date=start_iso,
                end_date=end_iso,
                customer_segment=request.customer_segment,
                customer_codes=None,
                customer_names=None,
                exclude_customer_codes=request.exclude_customer_codes,
                exclude_customer_names=request.exclude_customer_names,
            )
        )
        codes: list[str] = []
        seen: set[str] = set()
        for row in ranking:
            code = str(row.get("customer_code") or "").strip()
            if not code or code in seen:
                continue
            seen.add(code)
            codes.append(code)
            if len(codes) >= request.top_customers:
                break
        return codes, None

    @staticmethod
    def _paginate(
        cached: dict[str, Any],
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        all_items = list(cached.get("all_items") or [])
        total = len(all_items)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_rows = all_items[start_idx:end_idx]
        summary_base = dict(cached.get("summary_base") or {})
        summary_base["items_count"] = len(page_rows)
        return {
            "start_date": cached.get("start_date"),
            "end_date": cached.get("end_date"),
            "branch": cached.get("branch"),
            "granularity": cached.get("granularity"),
            "truncated": bool(cached.get("truncated")),
            "items": page_rows,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "has_more": end_idx < total,
            },
            "summary": summary_base,
        }
