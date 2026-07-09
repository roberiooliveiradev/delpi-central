from app.application.dto.commercial.sales_order_otd_request import SalesOrderOtdRequest
from app.domain.entities.commercial.sales_order_otd import SalesOrderOtd
from app.domain.ports.commercial.sales_order_otd_repository_port import SalesOrderOtdRepositoryPort
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.commercial_repositories.sales_order_otd_sql import (
    build_sales_order_otd_filters,
    build_sales_order_otd_sql,
)


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
