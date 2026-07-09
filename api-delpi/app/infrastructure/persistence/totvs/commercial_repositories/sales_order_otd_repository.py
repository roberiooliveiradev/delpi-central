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
    build_sales_order_otd_line_detail_sql,
    build_sales_order_otd_lines_count_sql,
    build_sales_order_otd_lines_list_sql,
    build_sales_order_otd_sql,
)
from app.infrastructure.persistence.totvs.pagination import paginate


class SalesOrderOtdRepository(BaseRepository, SalesOrderOtdRepositoryPort):
    def get_sales_order_otd(self, request: SalesOrderOtdRequest) -> SalesOrderOtd:
        where_clause, where_params = build_sales_order_otd_filters(
            branch=request.branch,
            start_date=request.start_date,
            end_date=request.end_date,
            customer_segment=request.customer_segment,
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
        )

        count_sql, count_reference_params = build_sales_order_otd_lines_count_sql(
            where_clause=where_clause,
            status=request.status,
            reference_end_date=request.end_date,
        )
        list_sql, list_reference_params = build_sales_order_otd_lines_list_sql(
            where_clause=where_clause,
            request=request,
            reference_end_date=request.end_date,
        )

        count_params = where_params + count_reference_params
        list_params = (
            where_params
            + list_reference_params
            + (paging["offset"], paging["page_size"])
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

    def get_sales_order_otd_line_detail(
        self,
        request: GetSalesOrderOtdLineDetailRequest,
    ) -> Optional[dict]:
        sql, params = build_sales_order_otd_line_detail_sql(
            branch=request.branch,
            order_number=request.order_number,
            line_item=request.line_item,
            reference_end_date=request.end_date,
        )

        with self:
            return self.execute_one(sql, params)
