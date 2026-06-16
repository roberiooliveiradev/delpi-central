from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder
from app.infrastructure.persistence.totvs.pagination import paginate
from app.infrastructure.persistence.totvs.production_repositories.production_pa_sql_filters import (
    SC2_MOTHER_OP_SEQUENCE_SQL,
    SC2_PA_PRODUCT_CODE_PREFIX_SQL,
)
from app.application.dto.production.get_production_otd_request import (
    GetProductionOtdRequest,
)
from app.application.dto.production.production_request import ProductionRequest
from app.application.models.page import Page
from app.domain.entities.production.on_time_delivery import OnTimeDelivery
from app.domain.ports.production.on_time_delivery_repository_port import (
    OnTimeDeliveryRepositoryPort,
)

_SC2_PA_JOIN = """
    INNER JOIN SB1010 P_PA
        ON P_PA.B1_COD = OP.C2_PRODUTO
       AND P_PA.D_E_L_E_T_ = ''
       AND P_PA.B1_TIPO = 'PA'
"""

_LIST_OPS_CTE = f"""
    OPS_KEYS AS (
        SELECT
            OP.C2_FILIAL AS branch,
            RTRIM(LTRIM(OP.C2_NUM)) AS order_number,
            RTRIM(LTRIM(OP.C2_ITEM)) AS order_item,
            MIN(RTRIM(LTRIM(OP.C2_OP))) AS production_order,
            OP.C2_DATPRF,
            OP.C2_DATRF,
            MIN(RTRIM(LTRIM(OP.C2_PRODUTO))) AS product_code
        FROM SC2010 OP
        {{pa_join}}
        WHERE {{where_clause}}
        GROUP BY
            OP.C2_FILIAL,
            OP.C2_NUM,
            OP.C2_ITEM,
            OP.C2_DATPRF,
            OP.C2_DATRF
    ),
    OPS_FINALIZADAS AS (
        SELECT
            k.branch,
            k.production_order,
            k.order_number,
            k.order_item,
            k.product_code,
            RTRIM(LTRIM(P_PA.B1_DESC)) AS product_description,
            CONVERT(VARCHAR(10), CONVERT(DATE, k.C2_DATPRF, 112), 23) AS due_date,
            CONVERT(VARCHAR(10), CONVERT(DATE, k.C2_DATRF, 112), 23) AS finish_date,
            DATEDIFF(
                DAY,
                CONVERT(DATE, k.C2_DATPRF, 112),
                CONVERT(DATE, k.C2_DATRF, 112)
            ) AS days_diff,
            CASE
                WHEN CONVERT(DATE, k.C2_DATRF, 112) <= CONVERT(DATE, k.C2_DATPRF, 112)
                THEN 'on_time'
                ELSE 'late'
            END AS status
        FROM OPS_KEYS k
        LEFT JOIN SB1010 P_PA
            ON P_PA.B1_COD = k.product_code
           AND P_PA.D_E_L_E_T_ = ''
    )
"""


class OnTimeDeliveryRepository(BaseRepository, OnTimeDeliveryRepositoryPort):

    def _build_base_where(
        self,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> tuple[str, tuple]:
        qb = QueryBuilder()
        qb.raw("OP.D_E_L_E_T_ = ''")

        if branch:
            qb.eq("OP.C2_FILIAL", branch)

        qb.raw("OP.C2_DATPRF IS NOT NULL")
        qb.raw("OP.C2_DATRF IS NOT NULL")
        qb.date_range("OP.C2_DATPRF", start_date, end_date)
        qb.raw(SC2_PA_PRODUCT_CODE_PREFIX_SQL)
        qb.raw(SC2_MOTHER_OP_SEQUENCE_SQL)

        return qb.build()

    @staticmethod
    def _status_filter_clause(status: str | None) -> str:
        normalized = (status or "").strip().lower()
        if normalized == "on_time":
            return "WHERE status = 'on_time'"
        if normalized == "late":
            return "WHERE status = 'late'"
        return ""

    @staticmethod
    def _list_order_clause(request: GetProductionOtdRequest) -> str:
        sort_columns = {
            "status": "status",
            "branch": "branch",
            "production_order": "production_order",
            "order_number": "order_number",
            "order_item": "order_item",
            "product_code": "product_code",
            "product_description": "product_description",
            "due_date": "due_date",
            "finish_date": "finish_date",
            "days_diff": "days_diff",
        }
        sort_key = (request.sort_by or "").strip().lower()
        sort_column = sort_columns.get(sort_key)
        if sort_column:
            direction = (
                "DESC" if str(request.sort_dir or "asc").lower() == "desc" else "ASC"
            )
            return f"""
                ORDER BY {sort_column} {direction}, order_number ASC, order_item ASC
            """

        normalized = (request.status or "").strip().lower()
        if normalized == "late":
            return """
                ORDER BY days_diff DESC, finish_date DESC, order_number ASC
            """
        if normalized == "on_time":
            return """
                ORDER BY finish_date DESC, order_number ASC, order_item ASC
            """
        return """
            ORDER BY due_date DESC, order_number ASC, order_item ASC
        """

    def get_on_time_delivery(
        self,
        request: ProductionRequest,
    ) -> OnTimeDelivery:
        where_clause, where_params = self._build_base_where(
            branch=request.branch,
            start_date=request.start_date,
            end_date=request.end_date,
        )

        sql = f"""
            WITH OPS_FINALIZADAS AS (
                SELECT DISTINCT
                    OP.C2_NUM,
                    OP.C2_DATPRF,
                    OP.C2_DATRF
                FROM SC2010 OP
                {_SC2_PA_JOIN}
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
        request: ProductionRequest,
    ) -> list[dict]:
        where_clause, where_params = self._build_base_where(
            branch=request.branch,
            start_date=request.start_date,
            end_date=request.end_date,
        )

        sql = f"""
            WITH OPS_FINALIZADAS AS (
                SELECT DISTINCT
                    OP.C2_FILIAL AS branch,
                    OP.C2_NUM,
                    OP.C2_DATPRF,
                    OP.C2_DATRF
                FROM SC2010 OP
                {_SC2_PA_JOIN}
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

    def list_production_orders_otd(
        self,
        request: GetProductionOtdRequest,
    ) -> Page[dict]:
        paging = paginate(request.page, request.page_size)
        where_clause, where_params = self._build_base_where(
            branch=request.branch,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        status_clause = self._status_filter_clause(request.status)
        order_clause = self._list_order_clause(request)
        list_cte = _LIST_OPS_CTE.format(
            pa_join=_SC2_PA_JOIN,
            where_clause=where_clause,
        )

        count_sql = f"""
            WITH {list_cte}
            SELECT COUNT(*) AS total
            FROM OPS_FINALIZADAS
            {status_clause}
        """

        list_sql = f"""
            WITH {list_cte}
            SELECT *
            FROM OPS_FINALIZADAS
            {status_clause}
            {order_clause}
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
