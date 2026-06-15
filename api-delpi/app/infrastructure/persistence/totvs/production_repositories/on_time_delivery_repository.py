from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder
from app.infrastructure.persistence.totvs.pagination import paginate
from app.application.dto.production.get_production_otd_request import (
    GetProductionOtdRequest,
)
from app.application.dto.production.production_request import ProductionRequest
from app.application.models.page import Page
from app.domain.entities.production.on_time_delivery import OnTimeDelivery
from app.domain.ports.production.on_time_delivery_repository_port import OnTimeDeliveryRepositoryPort


class OnTimeDeliveryRepository(BaseRepository, OnTimeDeliveryRepositoryPort):

    def get_on_time_delivery(
        self,
        request: ProductionRequest
    ) -> OnTimeDelivery:
        qb = QueryBuilder()
        qb.raw("OP.D_E_L_E_T_ = ''")

        if request.branch:
            qb.eq("OP.C2_FILIAL", request.branch)

        qb.raw("OP.C2_DATPRF IS NOT NULL")
        qb.raw("OP.C2_DATRF IS NOT NULL")
        qb.date_range("OP.C2_DATPRF", request.start_date, request.end_date)

        where_clause, where_params = qb.build()

        sql = f"""
            WITH OPS_FINALIZADAS AS (
                SELECT DISTINCT
                    OP.C2_NUM,
                    OP.C2_DATPRF,
                    OP.C2_DATRF
                FROM SC2010 OP
                WHERE {where_clause}
            )
            SELECT
                COUNT(*) AS total_ops_finished,
                SUM(CASE WHEN C2_DATRF <= C2_DATPRF THEN 1 ELSE 0 END) AS on_time_ops,
                SUM(CASE WHEN C2_DATRF > C2_DATPRF THEN 1 ELSE 0 END) AS late_ops,
                CAST(
                    SUM(CASE WHEN C2_DATRF <= C2_DATPRF THEN 1 ELSE 0 END) * 100.0
                    / NULLIF(COUNT(*), 0)
                    AS DECIMAL(10, 2)
                ) AS on_time_delivery_pct
            FROM OPS_FINALIZADAS
        """

        with self:
            row = self.execute_one(sql, where_params)

        if row:
            return OnTimeDelivery(
                branch=request.branch,
                start_date=request.start_date,
                end_date=request.end_date,
                total_ops_finished=int(row.get("total_ops_finished") or 0),
                on_time_ops=int(row.get("on_time_ops") or 0),
                late_ops=int(row.get("late_ops") or 0),
                on_time_delivery_pct=row.get("on_time_delivery_pct"),
            )

        return OnTimeDelivery(
            branch=request.branch,
            start_date=request.start_date,
            end_date=request.end_date,
            total_ops_finished=0,
            on_time_ops=0,
            late_ops=0,
            on_time_delivery_pct=None,
        )

    def list_on_time_delivery_by_branch(
        self,
        request: ProductionRequest
    ) -> list[dict]:
        qb = QueryBuilder()
        qb.raw("OP.D_E_L_E_T_ = ''")

        if request.branch:
            qb.eq("OP.C2_FILIAL", request.branch)

        qb.raw("OP.C2_DATPRF IS NOT NULL")
        qb.raw("OP.C2_DATRF IS NOT NULL")
        qb.date_range("OP.C2_DATPRF", request.start_date, request.end_date)

        where_clause, where_params = qb.build()

        sql = f"""
            WITH OPS_FINALIZADAS AS (
                SELECT DISTINCT
                    OP.C2_FILIAL AS branch,
                    OP.C2_NUM,
                    OP.C2_DATPRF,
                    OP.C2_DATRF
                FROM SC2010 OP
                WHERE {where_clause}
            )
            SELECT
                branch,
                COUNT(*) AS total_ops_finished,
                SUM(CASE WHEN C2_DATRF <= C2_DATPRF THEN 1 ELSE 0 END) AS on_time_ops,
                SUM(CASE WHEN C2_DATRF > C2_DATPRF THEN 1 ELSE 0 END) AS late_ops,
                CAST(
                    SUM(CASE WHEN C2_DATRF <= C2_DATPRF THEN 1 ELSE 0 END) * 100.0
                    / NULLIF(COUNT(*), 0)
                    AS DECIMAL(10, 2)
                ) AS on_time_delivery_pct
            FROM OPS_FINALIZADAS
            WHERE branch IS NOT NULL
            AND LTRIM(RTRIM(branch)) <> ''
            GROUP BY branch
            ORDER BY branch
        """

        with self:
            rows = self.execute_query(sql, where_params)

        return rows or []

    def _build_orders_where(
        self,
        request: GetProductionOtdRequest,
    ) -> tuple[str, tuple]:
        qb = QueryBuilder()
        qb.raw("OP.D_E_L_E_T_ = ''")

        if request.branch:
            qb.eq("OP.C2_FILIAL", request.branch)

        qb.raw("OP.C2_DATPRF IS NOT NULL")
        qb.raw("OP.C2_DATRF IS NOT NULL")
        qb.date_range("OP.C2_DATPRF", request.start_date, request.end_date)

        status = (request.status or "").strip().lower()
        if status == "on_time":
            qb.raw("OP.C2_DATRF <= OP.C2_DATPRF")
        elif status == "late":
            qb.raw("OP.C2_DATRF > OP.C2_DATPRF")

        return qb.build()

    def list_production_orders_otd(
        self,
        request: GetProductionOtdRequest,
    ) -> Page[dict]:
        paging = paginate(request.page, request.page_size)
        where_clause, where_params = self._build_orders_where(request)

        count_sql = f"""
            WITH OPS_FINALIZADAS AS (
                SELECT DISTINCT
                    OP.C2_FILIAL,
                    OP.C2_NUM,
                    OP.C2_ITEM
                FROM SC2010 OP
                WHERE {where_clause}
            )
            SELECT COUNT(*) AS total
            FROM OPS_FINALIZADAS
        """

        list_sql = f"""
            WITH OPS_FINALIZADAS AS (
                SELECT DISTINCT
                    OP.C2_FILIAL AS branch,
                    RTRIM(LTRIM(OP.C2_NUM)) AS order_number,
                    RTRIM(LTRIM(OP.C2_ITEM)) AS order_item,
                    RTRIM(LTRIM(OP.C2_PRODUTO)) AS product_code,
                    RTRIM(LTRIM(P.B1_DESC)) AS product_description,
                    CONVERT(VARCHAR(10), CONVERT(DATE, OP.C2_DATPRF, 112), 23) AS due_date,
                    CONVERT(VARCHAR(10), CONVERT(DATE, OP.C2_DATRF, 112), 23) AS finish_date,
                    DATEDIFF(
                        DAY,
                        CONVERT(DATE, OP.C2_DATPRF, 112),
                        CONVERT(DATE, OP.C2_DATRF, 112)
                    ) AS days_diff,
                    CASE
                        WHEN CONVERT(DATE, OP.C2_DATRF, 112) <= CONVERT(DATE, OP.C2_DATPRF, 112)
                        THEN 'on_time'
                        ELSE 'late'
                    END AS status
                FROM SC2010 OP
                LEFT JOIN SB1010 P
                    ON P.B1_COD = OP.C2_PRODUTO
                   AND P.D_E_L_E_T_ = ''
                WHERE {where_clause}
            )
            SELECT *
            FROM OPS_FINALIZADAS
            ORDER BY
                CASE WHEN status = 'late' THEN 0 ELSE 1 END,
                days_diff DESC,
                finish_date DESC,
                order_number ASC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """

        list_params = where_params + (paging["offset"], paging["page_size"])

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