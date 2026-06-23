from app.application.dto.commercial.sales_conversion_rate_request import SalesConversionRateRequest
from app.domain.entities.commercial.sales_conversion_rate import SalesConversionRate
from app.domain.ports.commercial.sales_conversion_rate_repository_port import SalesConversionRateRepositoryPort
from app.domain.services.commercial_customer_segment_service import (
    CommercialCustomerSegmentService,
)
from app.domain.services.commercial_proposal_status import WON_STATUS_CODE
from app.domain.services.commercial_proposal_acceptance_date_service import (
    CommercialProposalAcceptanceDateService,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder


class SalesConversionRateRepository(BaseRepository, SalesConversionRateRepositoryPort):

    def get_sales_conversion_rate(
        self,
        request: SalesConversionRateRequest
    ) -> SalesConversionRate:
        opened_qb = QueryBuilder()
        opened_qb.raw("AD1.D_E_L_E_T_ = ''")

        if request.branch:
            opened_qb.eq("AD1.AD1_FILIAL", request.branch)

        opened_qb.date_range("AD1.AD1_DATA", request.start_date, request.end_date)

        CommercialCustomerSegmentService.apply_segment_to_query_builder(
            opened_qb,
            "AD1.AD1_CODCLI",
            request.customer_segment,
        )

        opened_where, opened_params = opened_qb.build()

        acceptance_expr = CommercialProposalAcceptanceDateService.sql_acceptance_date_for_alias(
            "AD1"
        )

        won_qb = QueryBuilder()
        won_qb.raw("AD1.D_E_L_E_T_ = ''")

        if request.branch:
            won_qb.eq("AD1.AD1_FILIAL", request.branch)

        won_qb.eq("AD1.AD1_STATUS", WON_STATUS_CODE)
        won_qb.raw(f"({acceptance_expr}) IS NOT NULL")
        won_qb.raw(f"RTRIM(CAST(({acceptance_expr}) AS VARCHAR(20))) <> ''")
        won_qb.date_range(f"({acceptance_expr})", request.start_date, request.end_date)

        CommercialCustomerSegmentService.apply_segment_to_query_builder(
            won_qb,
            "AD1.AD1_CODCLI",
            request.customer_segment,
        )

        won_where, won_params = won_qb.build()

        sql = f"""
            WITH ovs_opened AS (
                SELECT DISTINCT
                    AD1.AD1_FILIAL,
                    AD1.AD1_NROPOR,
                    AD1.AD1_REVISA
                FROM AD1010 AD1
                WHERE {opened_where}
            ),
            ovs_won_accepted AS (
                SELECT DISTINCT
                    AD1.AD1_FILIAL,
                    AD1.AD1_NROPOR,
                    AD1.AD1_REVISA
                FROM AD1010 AD1
                WHERE {won_where}
            ),
            ovs_won_latest AS (
                SELECT
                    AD1_FILIAL,
                    AD1_NROPOR,
                    ROW_NUMBER() OVER (
                        PARTITION BY AD1_FILIAL, AD1_NROPOR
                        ORDER BY AD1_REVISA DESC
                    ) AS rn
                FROM ovs_won_accepted
            ),
            metrics AS (
                SELECT
                    (SELECT COUNT(*) FROM ovs_opened) AS qtd_proposals,
                    (
                        SELECT COUNT(*)
                        FROM ovs_won_latest
                        WHERE rn = 1
                    ) AS qtd_won
            )
            SELECT
                qtd_proposals,
                qtd_won,
                CAST(
                    CASE
                        WHEN qtd_proposals = 0 THEN 0
                        ELSE qtd_won * 100.0 / qtd_proposals
                    END
                AS DECIMAL(10, 2)) AS sales_conversion_rate_pct
            FROM metrics
        """

        params = tuple(opened_params) + tuple(won_params)

        with self:
            row = self.execute_one(sql, params)

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
