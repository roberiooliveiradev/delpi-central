from app.application.dto.supplies.get_purchase_order_otd_panel_request import (
    GetPurchaseOrderOtdPanelRequest,
)
from app.application.dto.supplies.purchase_order_otd_request import PurchaseOrderOtdRequest
from app.application.models.page import Page
from app.domain.entities.supplies.purchase_order_otd import PurchaseOrderOtd
from app.domain.ports.supplies.purchase_order_otd_repository_port import (
    PurchaseOrderOtdRepositoryPort,
)
from app.domain.totvs.protheus_product_types import PRODUCT_TYPE_RAW_MATERIAL
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.pagination import paginate
from app.infrastructure.persistence.totvs.supplies_repositories.purchase_order_otd_sql import (
    build_purchase_order_otd_filters,
    build_purchase_order_otd_lines_count_sql,
    build_purchase_order_otd_lines_list_sql,
    build_purchase_order_otd_sql,
)


class PurchaseOrderOtdRepository(BaseRepository, PurchaseOrderOtdRepositoryPort):
    def get_purchase_order_otd(self, request: PurchaseOrderOtdRequest) -> PurchaseOrderOtd:
        where_clause, where_params = build_purchase_order_otd_filters(
            branch=request.branch,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        sql = build_purchase_order_otd_sql(where_clause=where_clause)

        with self:
            row = self.execute_one(sql, where_params)

        if row:
            return PurchaseOrderOtd(
                branch=request.branch,
                start_date=request.start_date,
                end_date=request.end_date,
                product_type=PRODUCT_TYPE_RAW_MATERIAL,
                total_lines=int(row.get("total_lines") or 0),
                on_time_lines=int(row.get("on_time_lines") or 0),
                late_lines=int(row.get("late_lines") or 0),
                purchase_order_otd_pct=row.get("purchase_order_otd_pct"),
            )

        return PurchaseOrderOtd(
            branch=request.branch,
            start_date=request.start_date,
            end_date=request.end_date,
            product_type=PRODUCT_TYPE_RAW_MATERIAL,
            total_lines=0,
            on_time_lines=0,
            late_lines=0,
            purchase_order_otd_pct=None,
        )

    def list_purchase_order_otd_lines(
        self,
        request: GetPurchaseOrderOtdPanelRequest,
    ) -> Page[dict]:
        paging = paginate(request.page, request.page_size)
        where_clause, where_params = build_purchase_order_otd_filters(
            branch=request.branch,
            start_date=request.start_date,
            end_date=request.end_date,
        )

        count_sql = build_purchase_order_otd_lines_count_sql(
            where_clause=where_clause,
            status=request.status,
        )
        list_sql = build_purchase_order_otd_lines_list_sql(
            where_clause=where_clause,
            request=request,
        )

        list_params = tuple(where_params) + (paging["offset"], paging["page_size"])

        with self:
            total_row = self.execute_one(count_sql, where_params)
            total = int(total_row.get("total") or 0) if total_row else 0
            rows = self.execute_query(list_sql, list_params) or []

        return Page(
            items=rows,
            total=total,
            page=paging["page"],
            page_size=paging["page_size"],
        )
