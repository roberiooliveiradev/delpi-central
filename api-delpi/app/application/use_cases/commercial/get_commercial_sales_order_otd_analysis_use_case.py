from __future__ import annotations

from typing import Any, Optional

from app.application.dto.commercial.sales_order_otd_request import SalesOrderOtdRequest
from app.application.shared.chart_period_buckets import build_period_buckets
from app.application.use_cases.commercial.commercial_analysis_payload_helpers import (
    branch_breakdown_rows,
)
from app.application.use_cases.commercial.get_commercial_rol_analysis_use_case import (
    _to_iso_date,
)
from app.domain.services.commercial_analysis_filter_request import (
    CommercialAnalysisFilterRequest,
)
from app.infrastructure.persistence.totvs.commercial_repositories.sales_order_otd_repository import (
    SalesOrderOtdRepository,
)

FILIAL_01 = "01"
FILIAL_02 = "02"


class GetCommercialSalesOrderOtdAnalysisUseCase:
    def __init__(self, *, sales_order_otd_repository: SalesOrderOtdRepository) -> None:
        self._repository = sales_order_otd_repository

    def execute(self, request: CommercialAnalysisFilterRequest) -> dict[str, Any]:
        request.validate()
        start_iso = _to_iso_date(request.start_date)
        end_iso = _to_iso_date(request.end_date)

        summary = self._build_summary(request, start_iso=start_iso, end_iso=end_iso)
        series = self._build_series(request, start_iso=start_iso, end_iso=end_iso)
        by_customer, pagination = self._build_by_customer(
            request, start_iso=start_iso, end_iso=end_iso
        )

        payload: dict[str, Any] = {
            "summary": summary,
            "series": series,
            "by_customer": by_customer,
            "granularity": request.granularity,
            "group_by": request.group_by,
        }
        if pagination is not None:
            payload["pagination"] = pagination
        if request.group_by == "branch":
            payload["by_branch"] = branch_breakdown_rows(
                (summary or {}).get("by_branch") if isinstance(summary, dict) else None
            )
        return payload

    def _otd_request(
        self,
        request: CommercialAnalysisFilterRequest,
        *,
        branch: Optional[str],
        start_iso: Optional[str],
        end_iso: Optional[str],
    ) -> SalesOrderOtdRequest:
        return SalesOrderOtdRequest(
            branch=branch,
            start_date=start_iso,
            end_date=end_iso,
            customer_segment=request.customer_segment,
            customer_codes=request.customer_codes,
            customer_names=request.customer_names,
            exclude_customer_codes=request.exclude_customer_codes,
            exclude_customer_names=request.exclude_customer_names,
        )

    def _build_summary(
        self,
        request: CommercialAnalysisFilterRequest,
        *,
        start_iso: Optional[str],
        end_iso: Optional[str],
    ) -> dict[str, Any]:
        if request.branch:
            metrics = self._repository.get_sales_order_otd_analysis_summary(
                self._otd_request(
                    request,
                    branch=request.branch,
                    start_iso=start_iso,
                    end_iso=end_iso,
                )
            )
            totals = dict(metrics)
            by_branch = {f"branch_{request.branch}": dict(metrics)}
        else:
            metrics_01 = self._repository.get_sales_order_otd_analysis_summary(
                self._otd_request(
                    request,
                    branch=FILIAL_01,
                    start_iso=start_iso,
                    end_iso=end_iso,
                )
            )
            metrics_02 = self._repository.get_sales_order_otd_analysis_summary(
                self._otd_request(
                    request,
                    branch=FILIAL_02,
                    start_iso=start_iso,
                    end_iso=end_iso,
                )
            )
            totals = {
                "total_lines": int(metrics_01["total_lines"] + metrics_02["total_lines"]),
                "total_qty": round(metrics_01["total_qty"] + metrics_02["total_qty"], 2),
                "fulfilled_qty": round(
                    metrics_01["fulfilled_qty"] + metrics_02["fulfilled_qty"], 2
                ),
                "on_time_lines": int(
                    metrics_01["on_time_lines"] + metrics_02["on_time_lines"]
                ),
                "late_lines": int(metrics_01["late_lines"] + metrics_02["late_lines"]),
                "fulfillment_pct": None,
                "otd_pct": None,
            }
            denom_qty = totals["total_qty"]
            if denom_qty:
                totals["fulfillment_pct"] = round(
                    totals["fulfilled_qty"] * 100.0 / denom_qty, 2
                )
            lines = totals["total_lines"]
            if lines:
                totals["otd_pct"] = round(totals["on_time_lines"] * 100.0 / lines, 2)
            by_branch = {"branch_01": metrics_01, "branch_02": metrics_02}
        return {
            "start_date": start_iso or request.start_date,
            "end_date": end_iso or request.end_date,
            "branch": request.branch,
            "customer_segment": request.customer_segment,
            "totals": totals,
            "by_branch": by_branch,
        }

    def _build_series(
        self,
        request: CommercialAnalysisFilterRequest,
        *,
        start_iso: Optional[str],
        end_iso: Optional[str],
    ) -> list[dict[str, Any]]:
        buckets = build_period_buckets(
            start_date=start_iso,
            end_date=end_iso,
            granularity=request.granularity,
        )
        points: list[dict[str, Any]] = []
        for bucket in buckets.buckets:
            metrics_01 = None
            metrics_02 = None
            if request.branch in (None, FILIAL_01):
                metrics_01 = self._repository.get_sales_order_otd_analysis_summary(
                    self._otd_request(
                        request,
                        branch=FILIAL_01,
                        start_iso=bucket.start_date,
                        end_iso=bucket.end_date,
                    )
                )
            if request.branch in (None, FILIAL_02):
                metrics_02 = self._repository.get_sales_order_otd_analysis_summary(
                    self._otd_request(
                        request,
                        branch=FILIAL_02,
                        start_iso=bucket.start_date,
                        end_iso=bucket.end_date,
                    )
                )
            # Prefer explicit branch metrics for series row fields used by slides.
            primary = metrics_01 if request.branch != FILIAL_02 else metrics_02
            if request.branch is None and metrics_01 and metrics_02:
                primary = {
                    "total_qty": round(
                        metrics_01["total_qty"] + metrics_02["total_qty"], 2
                    ),
                    "fulfilled_qty": round(
                        metrics_01["fulfilled_qty"] + metrics_02["fulfilled_qty"], 2
                    ),
                    "fulfillment_pct": None,
                    "otd_pct": None,
                }
                denom_qty = primary["total_qty"]
                if denom_qty:
                    primary["fulfillment_pct"] = round(
                        primary["fulfilled_qty"] * 100.0 / denom_qty, 2
                    )
                lines = metrics_01["total_lines"] + metrics_02["total_lines"]
                on_time = metrics_01["on_time_lines"] + metrics_02["on_time_lines"]
                if lines:
                    primary["otd_pct"] = round(on_time * 100.0 / lines, 2)
            points.append(
                {
                    "period_label": bucket.label,
                    "sort_key": bucket.key,
                    "start_date": bucket.start_date,
                    "end_date": bucket.end_date,
                    "total_qty": (primary or {}).get("total_qty"),
                    "fulfilled_qty": (primary or {}).get("fulfilled_qty"),
                    "fulfillment_pct": (primary or {}).get("fulfillment_pct"),
                    "otd_pct": (primary or {}).get("otd_pct"),
                    "branch_01": metrics_01,
                    "branch_02": metrics_02,
                }
            )
        return points

    def _build_by_customer(
        self,
        request: CommercialAnalysisFilterRequest,
        *,
        start_iso: Optional[str],
        end_iso: Optional[str],
    ) -> tuple[list[dict[str, Any]], Optional[dict[str, Any]]]:
        if request.group_by != "customer":
            return [], None
        rows = self._repository.list_sales_order_otd_analysis_by_customer(
            self._otd_request(
                request,
                branch=request.branch,
                start_iso=start_iso,
                end_iso=end_iso,
            )
        )
        total = len(rows)
        start_idx = (request.page - 1) * request.page_size
        end_idx = start_idx + request.page_size
        page_rows = rows[start_idx:end_idx]
        return page_rows, {
            "page": request.page,
            "page_size": request.page_size,
            "total": total,
            "has_more": end_idx < total,
        }
