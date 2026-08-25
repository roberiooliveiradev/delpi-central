"""Weekly delivery portfolio forecast from SC5/SC6 open (or planned) order value."""

from __future__ import annotations

from typing import Optional

from app.domain.entities.commercial.weekly_portfolio import WeeklyPortfolioCustomerForecast
from app.domain.ports.commercial.commercial_weekly_portfolio_repository_port import (
    CommercialWeeklyPortfolioRepositoryPort,
)
from app.domain.services.commercial_analysis_filter_request import (
    CommercialAnalysisFilterRequest,
)
from app.domain.services.commercial_analysis_filter_service import (
    CommercialAnalysisFilterService,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder


class CommercialWeeklyPortfolioRepository(
    BaseRepository,
    CommercialWeeklyPortfolioRepositoryPort,
):
    def list_delivery_week_forecast_by_customer(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: Optional[str],
        filters: CommercialAnalysisFilterRequest,
        open_only: bool = False,
    ) -> list[WeeklyPortfolioCustomerForecast]:
        qb = QueryBuilder()
        qb.raw("C6.D_E_L_E_T_ = ''")
        qb.raw("C5.D_E_L_E_T_ = ''")
        qb.raw("C6.C6_QTDVEN > 0")
        qb.raw("C6.C6_ENTREG IS NOT NULL")
        qb.raw("RTRIM(CAST(C6.C6_ENTREG AS VARCHAR(20))) <> ''")
        qb.raw("(C6.C6_BLOQUEI IS NULL OR RTRIM(C6.C6_BLOQUEI) = '')")
        qb.raw("(C6.C6_BLQ IS NULL OR RTRIM(C6.C6_BLQ) = '')")
        if branch:
            qb.eq("C6.C6_FILIAL", branch)
        qb.date_range("C6.C6_ENTREG", start_date, end_date)
        if open_only:
            qb.raw("(C6.C6_QTDVEN - ISNULL(C6.C6_QTDENT, 0)) > 0")
        CommercialAnalysisFilterService.apply_from_request(
            qb,
            filters,
            customer_code_column="C5.C5_CLIENTE",
            customer_name_column="A1.A1_NOME",
        )
        where_clause, where_params = qb.build()

        qty_expr = (
            "(C6.C6_QTDVEN - ISNULL(C6.C6_QTDENT, 0))"
            if open_only
            else "C6.C6_QTDVEN"
        )
        sql = f"""
            SELECT
                RTRIM(C5.C5_CLIENTE) AS customer_code,
                ISNULL(
                    NULLIF(RTRIM(A1.A1_NREDUZ), ''),
                    ISNULL(RTRIM(A1.A1_NOME), RTRIM(C5.C5_CLIENTE))
                ) AS customer_name,
                RTRIM(C6.C6_FILIAL) AS branch,
                SUM(CONVERT(FLOAT, {qty_expr} * ISNULL(C6.C6_PRCVEN, 0))) AS forecast_value
            FROM SC6010 C6 WITH (NOLOCK)
            INNER JOIN SC5010 C5 WITH (NOLOCK)
                ON  C5.C5_FILIAL = C6.C6_FILIAL
                AND C5.C5_NUM = C6.C6_NUM
                AND C5.D_E_L_E_T_ = ''
            LEFT JOIN SA1010 A1 WITH (NOLOCK)
                ON  A1.D_E_L_E_T_ = ''
                AND A1.A1_COD = C5.C5_CLIENTE
                AND A1.A1_LOJA = C5.C5_LOJACLI
            WHERE {where_clause}
            GROUP BY C5.C5_CLIENTE, A1.A1_NREDUZ, A1.A1_NOME, C6.C6_FILIAL
            HAVING SUM(CONVERT(FLOAT, {qty_expr} * ISNULL(C6.C6_PRCVEN, 0))) <> 0
            ORDER BY forecast_value DESC, customer_code ASC
        """
        with self as repo:
            rows = repo.execute_query(sql, where_params) or []

        return [
            WeeklyPortfolioCustomerForecast(
                customer_code=str(row.get("customer_code") or "").strip(),
                customer_name=str(row.get("customer_name") or "").strip(),
                branch=str(row.get("branch") or "").strip(),
                forecast_value=round(float(row.get("forecast_value") or 0), 2),
            )
            for row in rows
        ]
