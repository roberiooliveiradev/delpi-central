from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder
from app.application.dto.commercial.sales_conversion_rate_request import SalesConversionRateRequest
from app.domain.entities.commercial.sales_conversion_rate import SalesConversionRate
from app.domain.ports.commercial.sales_conversion_rate_repository_port import SalesConversionRateRepositoryPort


class SalesConversionRateRepository(BaseRepository, SalesConversionRateRepositoryPort):

    def get_sales_conversion_rate(
        self,
        request: SalesConversionRateRequest
    ) -> SalesConversionRate:
        qb = QueryBuilder()
        qb.raw("AD1.D_E_L_E_T_ = ''")
        qb.eq("AD1.AD1_FILIAL", request.branch)
        qb.date_range("AD1.AD1_DATA", request.start_date, request.end_date)

        where_clause, where_params = qb.build()

        sql = f"""
            WITH ovs_base AS (
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
                SUM(CASE WHEN AD1_STATUS = '9' THEN 1 ELSE 0 END) AS qtd_won,
                CAST(
                    CASE
                        WHEN COUNT(*) = 0 THEN 0
                        ELSE SUM(CASE WHEN AD1_STATUS = '9' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)
                    END
                AS DECIMAL(10, 2)) AS sales_conversion_rate_pct
            FROM ovs_base
        """

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