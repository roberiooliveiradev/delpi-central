from si_app.infrastructure.persistence.totvs.base_repository import BaseRepository
from si_app.infrastructure.persistence.totvs.query_builder import QueryBuilder
from si_app.application.dto.production.production_request import ProductionRequest
from si_app.domain.entities.production.on_time_delivery import OnTimeDelivery
from si_app.domain.ports.production.on_time_delivery_repository_port import OnTimeDeliveryRepositoryPort


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