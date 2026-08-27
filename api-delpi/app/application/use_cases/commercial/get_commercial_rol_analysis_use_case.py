from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Optional

from app.application.dto.commercial.commercial_rol_series_request import (
    CommercialRolSeriesRequest,
)
from app.application.dto.commercial.get_rol_by_customer_request import (
    GetRolByCustomerRequest,
)
from app.application.dto.financial.get_rol_request import GetRolRequest
from app.application.use_cases.commercial.get_commercial_rol_by_customer_use_case import (
    GetCommercialRolByCustomerUseCase,
)
from app.application.use_cases.commercial.get_commercial_rol_series_use_case import (
    GetCommercialRolSeriesUseCase,
)
from app.domain.entities.commercial.weekly_portfolio import (
    WeeklyPortfolioBranchTotals,
    WeeklyPortfolioSnapshot,
)
from app.domain.ports.commercial.commercial_weekly_portfolio_repository_port import (
    CommercialWeeklyPortfolioRepositoryPort,
)
from app.domain.ports.financial.financial_query_repository_port import (
    FinancialQueryRepositoryPort,
)
from app.domain.services.commercial_analysis_filter_request import (
    CommercialAnalysisFilterRequest,
)

HEAD_OFFICE_BRANCH = "01"
BRANCH_OFFICE_BRANCH = "02"


def _to_iso_date(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    raw = str(value).strip()
    if len(raw) == 8 and raw.isdigit():
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
    return raw


def _parse_date(value: Optional[str]) -> Optional[date]:
    iso = _to_iso_date(value)
    if not iso:
        return None
    try:
        return date.fromisoformat(iso)
    except ValueError:
        return None


def _iso_week_bounds(anchor: date) -> tuple[date, date]:
    start = anchor - timedelta(days=anchor.weekday())
    end = start + timedelta(days=6)
    return start, end


class GetCommercialRolAnalysisUseCase:
    def __init__(
        self,
        *,
        financial_query_repository: FinancialQueryRepositoryPort,
        rol_series_use_case: GetCommercialRolSeriesUseCase,
        rol_by_customer_use_case: GetCommercialRolByCustomerUseCase,
        weekly_portfolio_repository: CommercialWeeklyPortfolioRepositoryPort,
    ) -> None:
        self._financial = financial_query_repository
        self._rol_series = rol_series_use_case
        self._rol_by_customer = rol_by_customer_use_case
        self._portfolio = weekly_portfolio_repository

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
        if request.include_portfolio:
            payload["portfolio"] = self._build_portfolio(request).to_dict()
        return payload

    def _filter_kwargs(self, request: CommercialAnalysisFilterRequest) -> dict[str, Any]:
        return {
            "customer_segment": request.customer_segment,
            "customer_codes": request.customer_codes,
            "customer_names": request.customer_names,
            "exclude_customer_codes": request.exclude_customer_codes,
            "exclude_customer_names": request.exclude_customer_names,
        }

    def _rol_metrics(self, rol: dict[str, Any]) -> dict[str, float]:
        return {
            "rol": round(float(rol.get("rol") or 0), 2),
            "gross_revenue": round(float(rol.get("gross_revenue") or 0), 2),
            "returns": round(float(rol.get("returns") or 0), 2),
            "discounts": round(float(rol.get("discounts") or 0), 2),
        }

    def _build_summary(
        self,
        request: CommercialAnalysisFilterRequest,
        *,
        start_iso: Optional[str],
        end_iso: Optional[str],
    ) -> dict[str, Any]:
        filters = self._filter_kwargs(request)
        if request.branch:
            rol = self._financial.get_rol(
                GetRolRequest(
                    branch=request.branch,
                    start_date=start_iso,
                    end_date=end_iso,
                    **filters,
                )
            )
            totals = self._rol_metrics(rol)
            by_branch = {f"branch_{request.branch}": totals}
        else:
            rol_01 = self._financial.get_rol(
                GetRolRequest(
                    branch=HEAD_OFFICE_BRANCH,
                    start_date=start_iso,
                    end_date=end_iso,
                    **filters,
                )
            )
            rol_02 = self._financial.get_rol(
                GetRolRequest(
                    branch=BRANCH_OFFICE_BRANCH,
                    start_date=start_iso,
                    end_date=end_iso,
                    **filters,
                )
            )
            m01 = self._rol_metrics(rol_01)
            m02 = self._rol_metrics(rol_02)
            totals = {
                key: round(m01[key] + m02[key], 2) for key in m01
            }
            by_branch = {"branch_01": m01, "branch_02": m02}

        return {
            "start_date": start_iso or request.start_date,
            "end_date": end_iso or request.end_date,
            "branch": request.branch,
            "customer_segment": request.customer_segment,
            "totals": totals,
            "by_branch": by_branch,
            **totals,
        }

    def _build_series(
        self,
        request: CommercialAnalysisFilterRequest,
        *,
        start_iso: Optional[str],
        end_iso: Optional[str],
    ) -> list[dict[str, Any]]:
        series_req = CommercialRolSeriesRequest(
            granularity=request.granularity,
            date_start=start_iso,
            date_end=end_iso,
            **self._filter_kwargs(request),
        )
        response = self._rol_series.execute(series_req)
        points: list[dict[str, Any]] = []
        for point in response.points:
            if request.branch == HEAD_OFFICE_BRANCH:
                branch_01 = {"rol": point.rol_matrix}
                branch_02 = {"rol": None}
            elif request.branch == BRANCH_OFFICE_BRANCH:
                branch_01 = {"rol": None}
                branch_02 = {"rol": point.rol_branch}
            else:
                branch_01 = {"rol": point.rol_matrix}
                branch_02 = {"rol": point.rol_branch}
            points.append(
                {
                    "period_label": point.periodo,
                    "sort_key": point.sort_key,
                    "start_date": point.start_date,
                    "end_date": point.end_date,
                    "branch_01": branch_01,
                    "branch_02": branch_02,
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

        if not start_iso or not end_iso:
            return [], {
                "page": request.page,
                "page_size": request.page_size,
                "total": 0,
                "has_more": False,
            }

        # Fetch enough rows for the requested page (no others bucket).
        fetch_limit = min(500, request.page * request.page_size)
        result = self._rol_by_customer.execute(
            GetRolByCustomerRequest(
                branch=request.branch,
                start_date=start_iso,
                end_date=end_iso,
                limit=fetch_limit,
                include_others=False,
                page=request.page,
                page_size=request.page_size,
                **self._filter_kwargs(request),
            )
        )
        total = int(result.customers_count)
        start_idx = (request.page - 1) * request.page_size
        end_idx = start_idx + request.page_size
        page_items = list(result.items)[start_idx:end_idx]
        rows = [
            {
                "customer_code": item.customer_code,
                "customer_store": item.customer_store,
                "customer_name": item.customer_name,
                "branch": result.branch,
                "rol": item.rol,
                "share_pct": item.share_pct,
                "rank": item.rank,
            }
            for item in page_items
        ]
        pagination = {
            "page": request.page,
            "page_size": request.page_size,
            "total": total,
            "has_more": end_idx < total,
        }
        return rows, pagination

    def _build_portfolio(
        self,
        request: CommercialAnalysisFilterRequest,
    ) -> WeeklyPortfolioSnapshot:
        anchor = _parse_date(request.end_date) or date.today()
        current_start, current_end = _iso_week_bounds(anchor)
        previous_start = current_start - timedelta(days=7)
        previous_end = current_end - timedelta(days=7)

        branches = (
            [request.branch]
            if request.branch
            else [HEAD_OFFICE_BRANCH, BRANCH_OFFICE_BRANCH]
        )
        previous_totals: list[WeeklyPortfolioBranchTotals] = []
        filters = self._filter_kwargs(request)

        for branch in branches:
            forecast_rows = self._portfolio.list_delivery_week_forecast_by_customer(
                start_date=previous_start.isoformat(),
                end_date=previous_end.isoformat(),
                branch=branch,
                filters=request,
                open_only=False,
            )
            forecast_value = round(
                sum(row.forecast_value for row in forecast_rows), 2
            )
            realized = self._financial.get_rol(
                GetRolRequest(
                    branch=branch,
                    start_date=previous_start.isoformat(),
                    end_date=previous_end.isoformat(),
                    **filters,
                )
            )
            realized_value = round(float(realized.get("rol") or 0), 2)
            previous_totals.append(
                WeeklyPortfolioBranchTotals(
                    branch=branch or "",
                    forecast_value=forecast_value,
                    realized_value=realized_value,
                    variance_value=round(realized_value - forecast_value, 2),
                )
            )

        current_forecast = self._portfolio.list_delivery_week_forecast_by_customer(
            start_date=current_start.isoformat(),
            end_date=current_end.isoformat(),
            branch=request.branch,
            filters=request,
            open_only=True,
        )
        return WeeklyPortfolioSnapshot(
            previous_week_by_branch=tuple(previous_totals),
            current_week_forecast=tuple(current_forecast),
        )
