from app.application.dto.commercial.sales_order_otd_request import SalesOrderOtdRequest
from app.domain.entities.commercial.sales_order_otd import SalesOrderOtd
from app.domain.ports.commercial.sales_order_otd_repository_port import SalesOrderOtdRepositoryPort
from app.domain.services.commercial_customer_segment_service import (
    CommercialCustomerSegmentService,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder


class SalesOrderOtdRepository(BaseRepository, SalesOrderOtdRepositoryPort):
    def get_sales_order_otd(self, request: SalesOrderOtdRequest) -> SalesOrderOtd:
        qb = QueryBuilder()
        qb.raw("C6.D_E_L_E_T_ = ''")
        qb.raw("C5.D_E_L_E_T_ = ''")
        qb.raw("C6.C6_QTDVEN > 0")
        qb.raw("C6.C6_QTDENT >= C6.C6_QTDVEN")
        qb.raw("C6.C6_ENTREG IS NOT NULL")
        qb.raw("RTRIM(CAST(C6.C6_ENTREG AS VARCHAR(20))) <> ''")
        qb.raw("C6.C6_DATFAT IS NOT NULL")
        qb.raw("RTRIM(CAST(C6.C6_DATFAT AS VARCHAR(20))) <> ''")
        qb.raw("(C6.C6_BLOQUEI IS NULL OR RTRIM(C6.C6_BLOQUEI) = '')")
        qb.raw("(C6.C6_BLQ IS NULL OR RTRIM(C6.C6_BLQ) = '')")

        if request.branch:
            qb.eq("C6.C6_FILIAL", request.branch)

        qb.date_range("C6.C6_ENTREG", request.start_date, request.end_date)

        CommercialCustomerSegmentService.apply_segment_to_query_builder(
            qb,
            "C5.C5_CLIENTE",
            request.customer_segment,
        )

        where_clause, where_params = qb.build()

        sql = f"""
            WITH linhas_entregues AS (
                SELECT DISTINCT
                    C6.C6_FILIAL,
                    C6.C6_NUM,
                    C6.C6_ITEM,
                    C6.C6_ENTREG,
                    C6.C6_DATFAT
                FROM SC6010 C6
                INNER JOIN SC5010 C5
                    ON  C5.C5_FILIAL = C6.C6_FILIAL
                    AND C5.C5_NUM = C6.C6_NUM
                WHERE {where_clause}
            )
            SELECT
                COUNT(*) AS total_lines,
                SUM(CASE WHEN C6_DATFAT <= C6_ENTREG THEN 1 ELSE 0 END) AS on_time_lines,
                SUM(CASE WHEN C6_DATFAT > C6_ENTREG THEN 1 ELSE 0 END) AS late_lines,
                CAST(
                    CASE
                        WHEN COUNT(*) = 0 THEN NULL
                        ELSE SUM(CASE WHEN C6_DATFAT <= C6_ENTREG THEN 1 ELSE 0 END) * 100.0
                             / COUNT(*)
                    END
                AS DECIMAL(10, 2)) AS sales_order_otd_pct
            FROM linhas_entregues
        """

        with self:
            row = self.execute_one(sql, where_params)

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
