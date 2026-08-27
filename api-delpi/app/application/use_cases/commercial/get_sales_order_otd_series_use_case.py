from __future__ import annotations

from typing import Any

from app.application.dto.commercial.sales_order_otd_request import SalesOrderOtdRequest
from app.application.dto.commercial.sales_order_otd_series_request import (
    SalesOrderOtdSeriesRequest,
)
from app.application.dto.commercial.sales_order_otd_series_response import (
    SalesOrderOtdSeriesPointDto,
    SalesOrderOtdSeriesResponse,
)
from app.application.services.charts.chart_series_cache_keys import (
    commercial_sales_order_otd_series_cache_key,
)
from app.application.services.production.production_kpi_cache import (
    get_cached_chart_series,
    set_cached_chart_series,
)
from app.application.shared.chart_period_buckets import build_period_buckets
from app.application.shared.numeric_parsing import to_optional_float
from app.domain.ports.commercial.sales_order_otd_repository_port import (
    SalesOrderOtdRepositoryPort,
)
from app.domain.totvs.protheus_branches import optional_concrete_branch

FILIAL_01 = "01"
FILIAL_02 = "02"


class GetSalesOrderOtdSeriesUseCase:
    def __init__(self, *, sales_order_otd_repository: SalesOrderOtdRepositoryPort):
        self._repository = sales_order_otd_repository

    def execute(self, request: SalesOrderOtdSeriesRequest) -> SalesOrderOtdSeriesResponse:
        request.validate()
        effective_branch = optional_concrete_branch(request.branch)

        cache_key = commercial_sales_order_otd_series_cache_key(request)
        cached = get_cached_chart_series(cache_key)
        if cached is not None:
            return self._from_cached_dict(cached)

        buckets_result = build_period_buckets(
            start_date=request.date_start,
            end_date=request.date_end,
            granularity=request.granularity,
        )

        points: list[SalesOrderOtdSeriesPointDto] = []

        for bucket in buckets_result.buckets:
            metrics_01 = self._fetch_metrics(
                branch=FILIAL_01,
                start_date=bucket.start_date,
                end_date=bucket.end_date,
                request=request,
                include=effective_branch in (None, FILIAL_01),
            )
            metrics_02 = self._fetch_metrics(
                branch=FILIAL_02,
                start_date=bucket.start_date,
                end_date=bucket.end_date,
                request=request,
                include=effective_branch in (None, FILIAL_02),
            )
            consolidated = self._consolidate(metrics_01, metrics_02, effective_branch)

            points.append(
                SalesOrderOtdSeriesPointDto(
                    periodo=bucket.label,
                    sort_key=bucket.key,
                    start_date=bucket.start_date,
                    end_date=bucket.end_date,
                    otd_filial_01=(
                        to_optional_float(metrics_01.get("otd_pct"))
                        if metrics_01 is not None
                        else None
                    ),
                    otd_filial_02=(
                        to_optional_float(metrics_02.get("otd_pct"))
                        if metrics_02 is not None
                        else None
                    ),
                    total_qty=consolidated.get("total_qty"),
                    fulfilled_qty=consolidated.get("fulfilled_qty"),
                    fulfillment_pct=consolidated.get("fulfillment_pct"),
                    otd_pct=consolidated.get("otd_pct"),
                    total_lines=consolidated.get("total_lines"),
                )
            )

        response = SalesOrderOtdSeriesResponse(
            granularity=request.granularity,
            truncated=buckets_result.truncated,
            branch=effective_branch,
            points=points,
        )
        set_cached_chart_series(cache_key, response.to_dict())
        return response

    @staticmethod
    def _from_cached_dict(cached: dict) -> SalesOrderOtdSeriesResponse:
        points: list[SalesOrderOtdSeriesPointDto] = []
        for point in cached.get("points") or []:
            if not isinstance(point, dict):
                continue
            points.append(
                SalesOrderOtdSeriesPointDto(
                    periodo=str(point.get("periodo") or ""),
                    sort_key=str(point.get("sort_key") or ""),
                    start_date=str(point.get("start_date") or ""),
                    end_date=str(point.get("end_date") or ""),
                    otd_filial_01=to_optional_float(point.get("otd_filial_01")),
                    otd_filial_02=to_optional_float(point.get("otd_filial_02")),
                    total_qty=to_optional_float(point.get("total_qty")),
                    fulfilled_qty=to_optional_float(point.get("fulfilled_qty")),
                    fulfillment_pct=to_optional_float(point.get("fulfillment_pct")),
                    otd_pct=to_optional_float(point.get("otd_pct")),
                    total_lines=(
                        int(point["total_lines"])
                        if point.get("total_lines") is not None
                        else None
                    ),
                )
            )
        return SalesOrderOtdSeriesResponse(
            granularity=cached["granularity"],
            truncated=bool(cached["truncated"]),
            branch=cached.get("branch"),
            points=points,
        )

    def _fetch_metrics(
        self,
        *,
        branch: str,
        start_date: str,
        end_date: str,
        request: SalesOrderOtdSeriesRequest,
        include: bool,
    ) -> dict[str, Any] | None:
        if not include:
            return None
        return self._repository.get_sales_order_otd_analysis_summary(
            SalesOrderOtdRequest(
                branch=branch,
                start_date=start_date,
                end_date=end_date,
                customer_segment=request.customer_segment,
                customer_codes=request.customer_codes,
                customer_names=request.customer_names,
                exclude_customer_codes=request.exclude_customer_codes,
                exclude_customer_names=request.exclude_customer_names,
            )
        )

    @staticmethod
    def _consolidate(
        metrics_01: dict[str, Any] | None,
        metrics_02: dict[str, Any] | None,
        branch: str | None,
    ) -> dict[str, Any]:
        if branch == FILIAL_02:
            primary = metrics_02 or {}
            return {
                "total_qty": to_optional_float(primary.get("total_qty")),
                "fulfilled_qty": to_optional_float(primary.get("fulfilled_qty")),
                "fulfillment_pct": to_optional_float(primary.get("fulfillment_pct")),
                "otd_pct": to_optional_float(primary.get("otd_pct")),
                "total_lines": (
                    int(primary["total_lines"])
                    if primary.get("total_lines") is not None
                    else None
                ),
            }
        if branch == FILIAL_01:
            primary = metrics_01 or {}
            return {
                "total_qty": to_optional_float(primary.get("total_qty")),
                "fulfilled_qty": to_optional_float(primary.get("fulfilled_qty")),
                "fulfillment_pct": to_optional_float(primary.get("fulfillment_pct")),
                "otd_pct": to_optional_float(primary.get("otd_pct")),
                "total_lines": (
                    int(primary["total_lines"])
                    if primary.get("total_lines") is not None
                    else None
                ),
            }

        m01 = metrics_01 or {}
        m02 = metrics_02 or {}
        total_qty = round(
            float(m01.get("total_qty") or 0) + float(m02.get("total_qty") or 0),
            2,
        )
        fulfilled_qty = round(
            float(m01.get("fulfilled_qty") or 0) + float(m02.get("fulfilled_qty") or 0),
            2,
        )
        total_lines = int(m01.get("total_lines") or 0) + int(m02.get("total_lines") or 0)
        on_time = int(m01.get("on_time_lines") or 0) + int(m02.get("on_time_lines") or 0)
        fulfillment_pct = (
            round(fulfilled_qty * 100.0 / total_qty, 2) if total_qty else None
        )
        otd_pct = round(on_time * 100.0 / total_lines, 2) if total_lines else None
        return {
            "total_qty": total_qty,
            "fulfilled_qty": fulfilled_qty,
            "fulfillment_pct": fulfillment_pct,
            "otd_pct": otd_pct,
            "total_lines": total_lines,
        }
