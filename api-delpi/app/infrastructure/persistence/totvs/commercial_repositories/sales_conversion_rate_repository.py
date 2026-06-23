from app.application.dto.commercial.sales_conversion_rate_request import SalesConversionRateRequest
from app.domain.entities.commercial.sales_conversion_rate import SalesConversionRate
from app.domain.ports.commercial.sales_conversion_rate_repository_port import SalesConversionRateRepositoryPort
from app.domain.services.commercial_customer_segment_service import (
    CommercialCustomerSegmentService,
)
from app.domain.services.commercial_proposal_status import WON_STATUS_CODE
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder


class SalesConversionRateRepository(BaseRepository, SalesConversionRateRepositoryPort):

    def get_sales_conversion_rate(
        self,
        request: SalesConversionRateRequest
    ) -> SalesConversionRate:
        qb = QueryBuilder()
        qb.raw("AD1.D_E_L_E_T_ = ''")

        if request.branch:
            qb.eq("AD1.AD1_FILIAL", request.branch)

        qb.date_range("AD1.AD1_DATA", request.start_date, request.end_date)

        CommercialCustomerSegmentService.apply_segment_to_query_builder(
            qb,
            "AD1.AD1_CODCLI",
            request.customer_segment,
        )

        where_clause, where_params = qb.build()

        won_qb = QueryBuilder()
        won_qb.raw(f"AD1_STATUS = '{WON_STATUS_CODE}'")
        won_qb.raw("AD1_DTFIM IS NOT NULL")
        won_qb.raw("RTRIM(CAST(AD1_DTFIM AS VARCHAR(20))) <> ''")
        won_qb.date_range("AD1_DTFIM", request.start_date, request.end_date)
        won_clause, won_params = won_qb.build()

        sql = f"""
            WITH ovs_opened AS (
                SELECT DISTINCT
                    AD1.AD1_FILIAL,
                    AD1.AD1_NROPOR,
                    AD1.AD1_REVISA,
                    AD1.AD1_DESCRI,
                    AD1.AD1_DATA,
                    AD1.AD1_DTFIM,
                    AD1.AD1_STATUS
                FROM AD1010 AD1
                WHERE {where_clause}
            )
            SELECT
                COUNT(*) AS qtd_proposals,
                SUM(CASE WHEN {won_clause} THEN 1 ELSE 0 END) AS qtd_won,
                CAST(
                    CASE
                        WHEN COUNT(*) = 0 THEN 0
                        ELSE SUM(CASE WHEN {won_clause} THEN 1 ELSE 0 END) * 100.0 / COUNT(*)
                    END
                AS DECIMAL(10, 2)) AS sales_conversion_rate_pct
            FROM ovs_opened
        """

        where_params = tuple(where_params) + tuple(won_params) + tuple(won_params)

        with self:
            row = self.execute_one(sql, where_params)

        if row:
            return SalesConversionRate(
                branch=request.branch,
                start_date=request.start_date,
                end_date=request.end_date,
                qtd_proposals=int(row.get("qtd_proposals") or 0),
                qtd_won=int(row.get("qtd_won") or 0),
                sales_conversion_rate_pct=row.get("sales_conversion_rate_pct"),
            )

        return SalesConversionRate(
            branch=request.branch,
            start_date=request.start_date,
            end_date=request.end_date,
            qtd_proposals=0,
            qtd_won=0,
            sales_conversion_rate_pct=0,
        )