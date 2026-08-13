from typing import Optional

from app.application.dto.commercial.get_sales_order_otd_line_detail_request import (
    GetSalesOrderOtdLineDetailRequest,
)
from app.application.dto.commercial.get_sales_order_otd_panel_request import (
    GetSalesOrderOtdPanelRequest,
)
from app.application.dto.commercial.sales_order_otd_request import SalesOrderOtdRequest
from app.application.models.page import Page
from app.domain.entities.commercial.sales_order_otd import SalesOrderOtd
from app.domain.ports.commercial.sales_order_otd_repository_port import (
    SalesOrderOtdRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.commercial_repositories.sales_order_otd_sql import (
    build_sales_order_otd_filters,
    build_sales_order_otd_late_days_stats_sql,
    build_sales_order_otd_line_detail_sql,
    build_sales_order_otd_line_detail_where,
    build_sales_order_otd_lines_count_sql,
    build_sales_order_otd_lines_list_sql,
    build_sales_order_otd_recurring_customers_sql,
    build_sales_order_otd_sql,
    build_sales_order_otd_upcoming_promises_sql,
    build_sales_order_otd_worst_delays_sql,
    compose_sales_order_otd_lines_params,
    sales_order_otd_search_params,
)
from app.infrastructure.persistence.totvs.pagination import paginate


def _optional_float(value) -> Optional[float]:
    if value is None:
        return None
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None


class SalesOrderOtdRepository(BaseRepository, SalesOrderOtdRepositoryPort):
    def get_sales_order_otd(self, request: SalesOrderOtdRequest) -> SalesOrderOtd:
        where_clause, where_params = build_sales_order_otd_filters(
            branch=request.branch,
            start_date=request.start_date,
            end_date=request.end_date,
            customer_segment=request.customer_segment,
            customer_codes=request.customer_codes,
        )

        sql, reference_params = build_sales_order_otd_sql(
            where_clause=where_clause,
            reference_end_date=request.end_date,
        )

        with self:
            row = self.execute_one(sql, where_params + reference_params)

        if row:
            return SalesOrderOtd(
                branch=request.branch,
                start_date=request.start_date,
                end_date=request.end_date,
                total_lines=int(row.get("total_lines") or 0),
                on_time_lines=int(row.get("on_time_lines") or 0),
                late_lines=int(row.get("late_lines") or 0),
                sales_order_otd_pct=row.get("sales_order_otd_pct"),
            )

        return SalesOrderOtd(
            branch=request.branch,
            start_date=request.start_date,
            end_date=request.end_date,
            total_lines=0,
            on_time_lines=0,
            late_lines=0,
            sales_order_otd_pct=None,
        )

    def list_sales_order_otd_lines(
        self,
        request: GetSalesOrderOtdPanelRequest,
    ) -> Page[dict]:
        paging = paginate(request.page, request.page_size)
        where_clause, where_params = build_sales_order_otd_filters(
            branch=request.branch,
            start_date=request.start_date,
            end_date=request.end_date,
            customer_segment=request.customer_segment,
            customer_codes=request.customer_codes,
        )
        search_params = sales_order_otd_search_params(request.search)

        count_sql, _ = build_sales_order_otd_lines_count_sql(
            where_clause=where_clause,
            status=request.status,
            reference_end_date=request.end_date,
            search=request.search,
        )
        list_sql, _ = build_sales_order_otd_lines_list_sql(
            where_clause=where_clause,
            request=request,
            reference_end_date=request.end_date,
        )

        count_params = compose_sales_order_otd_lines_params(
            where_params=where_params,
            reference_end_date=request.end_date,
            search_params=search_params,
        )
        list_params = compose_sales_order_otd_lines_params(
            where_params=where_params,
            reference_end_date=request.end_date,
            search_params=search_params,
            offset=paging["offset"],
            page_size=paging["page_size"],
        )

        with self:
            total_row = self.execute_one(count_sql, count_params)
            total = int(total_row.get("total") or 0) if total_row else 0
            rows = self.execute_query(list_sql, list_params) or []

        return Page(
            items=rows,
            total=total,
            page=paging["page"],
            page_size=paging["page_size"],
        )

    def get_sales_order_otd_late_days_stats(
        self,
        request: GetSalesOrderOtdPanelRequest,
    ) -> dict:
        where_clause, where_params = build_sales_order_otd_filters(
            branch=request.branch,
            start_date=request.start_date,
            end_date=request.end_date,
            customer_segment=request.customer_segment,
            customer_codes=request.customer_codes,
        )
        sql, _ = build_sales_order_otd_late_days_stats_sql(
            where_clause=where_clause,
            reference_end_date=request.end_date,
        )
        params = compose_sales_order_otd_lines_params(
            where_params=where_params,
            reference_end_date=request.end_date,
        )
        with self:
            row = self.execute_one(sql, params) or {}
        return {
            "avg_late_days": _optional_float(row.get("avg_late_days")),
            "p50_late_days": _optional_float(row.get("p50_late_days")),
            "p90_late_days": _optional_float(row.get("p90_late_days")),
        }

    def get_sales_order_otd_panel_insights(
        self,
        request: GetSalesOrderOtdPanelRequest,
    ) -> dict:
        where_clause, where_params = build_sales_order_otd_filters(
            branch=request.branch,
            start_date=request.start_date,
            end_date=request.end_date,
            customer_segment=request.customer_segment,
            customer_codes=request.customer_codes,
        )
        params = compose_sales_order_otd_lines_params(
            where_params=where_params,
            reference_end_date=request.end_date,
        )
        recurring_sql, _ = build_sales_order_otd_recurring_customers_sql(
            where_clause=where_clause,
            reference_end_date=request.end_date,
        )
        worst_sql, _ = build_sales_order_otd_worst_delays_sql(
            where_clause=where_clause,
            reference_end_date=request.end_date,
        )
        upcoming_sql, _ = build_sales_order_otd_upcoming_promises_sql(
            where_clause=where_clause,
            reference_end_date=request.end_date,
        )
        with self:
            recurring = self.execute_query(recurring_sql, params) or []
            worst = self.execute_query(worst_sql, params) or []
            upcoming = self.execute_query(upcoming_sql, params) or []
        return {
            "recurringCustomers": recurring,
            "worstDelays": worst,
            "upcomingPromises": upcoming,
        }

    def get_sales_order_otd_line_detail(
        self,
        request: GetSalesOrderOtdLineDetailRequest,
    ) -> Optional[dict]:
        where_clause, where_params = build_sales_order_otd_line_detail_where(
            branch=request.branch,
            order_number=request.order_number,
            line_item=request.line_item,
            start_date=request.start_date,
            end_date=request.end_date,
            customer_segment=request.customer_segment,
            customer_codes=request.customer_codes,
        )
        sql = build_sales_order_otd_line_detail_sql(where_clause=where_clause)
        params = compose_sales_order_otd_lines_params(
            where_params=where_params,
            reference_end_date=request.end_date,
        )

        with self:
            return self.execute_one(sql, params)
