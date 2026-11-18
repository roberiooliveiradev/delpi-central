"""Consulta fiscal consolidada de vendas por produto, filial e mês no Protheus."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.domain.services.commercial.commercial_rol_return_sql import CommercialRolReturnSql
from app.domain.services.product.product_sales_analytics import (
    first_day_of_window,
    summarize_product_sales,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository


class ProductSalesAnalyticsRepository(BaseRepository):
    def get_product_sales(self, *, branch: str, product_code: str, months: int) -> dict | None:
        today = datetime.now(ZoneInfo("America/Sao_Paulo")).date()
        start = first_day_of_window(months, today)
        begin_date = start.strftime("%Y%m%d")
        end_date = today.strftime("%Y%m%d")

        product_sql = """
            SELECT TOP 1 RTRIM(B1_COD) AS code, RTRIM(B1_DESC) AS description,
                   RTRIM(B1_UM) AS unit, RTRIM(B1_TIPO) AS product_type
            FROM SB1010
            WHERE D_E_L_E_T_ = '' AND B1_COD = ?
              AND B1_FILIAL IN ('', ?)
            ORDER BY CASE WHEN B1_FILIAL = ? THEN 0 ELSE 1 END
        """
        sales_eligibility = CommercialRolReturnSql.sale_eligibility_predicate(
            exists_where="D1X.D1_DTDIGIT BETWEEN ? AND ?"
        )
        return_eligibility = CommercialRolReturnSql.sales_return_predicate()
        sql = f"""
            SELECT movements.month, movements.customer_code, movements.customer_store,
                   MAX(movements.customer_name) AS customer_name,
                   SUM(movements.gross_quantity) AS gross_quantity,
                   SUM(movements.returned_quantity) AS returned_quantity
            FROM (
                SELECT SUBSTRING(D2.D2_EMISSAO, 1, 6) AS month,
                       D2.D2_CLIENTE AS customer_code, D2.D2_LOJA AS customer_store,
                       MAX(COALESCE(NULLIF(RTRIM(A1.A1_NREDUZ), ''),
                                    NULLIF(RTRIM(A1.A1_NOME), ''), D2.D2_CLIENTE)) AS customer_name,
                       SUM(CONVERT(FLOAT, ISNULL(D2.D2_QUANT, 0))) AS gross_quantity,
                       CONVERT(FLOAT, 0) AS returned_quantity
                FROM SD2010 D2 WITH (NOLOCK)
                {CommercialRolReturnSql.sale_tes_join()}
                {CommercialRolReturnSql.sale_customer_join()}
                WHERE D2.D_E_L_E_T_ = ''
                  AND D2.D2_FILIAL = ? AND D2.D2_COD = ?
                  AND D2.D2_EMISSAO BETWEEN ? AND ?
                  AND {sales_eligibility}
                GROUP BY SUBSTRING(D2.D2_EMISSAO, 1, 6), D2.D2_CLIENTE, D2.D2_LOJA

                UNION ALL

                SELECT SUBSTRING(D1.D1_DTDIGIT, 1, 6) AS month,
                       D1.D1_FORNECE AS customer_code, D1.D1_LOJA AS customer_store,
                       MAX(COALESCE(NULLIF(RTRIM(A1D.A1_NREDUZ), ''),
                                    NULLIF(RTRIM(A1D.A1_NOME), ''), D1.D1_FORNECE)) AS customer_name,
                       CONVERT(FLOAT, 0) AS gross_quantity,
                       SUM(CONVERT(FLOAT, ISNULL(D1.D1_QUANT, 0))) AS returned_quantity
                FROM SD1010 D1 WITH (NOLOCK)
                LEFT JOIN SA1010 A1D WITH (NOLOCK)
                    ON A1D.D_E_L_E_T_ = '' AND A1D.A1_COD = D1.D1_FORNECE AND A1D.A1_LOJA = D1.D1_LOJA
                {CommercialRolReturnSql.tes_join()}
                {CommercialRolReturnSql.product_type_join()}
                WHERE D1.D_E_L_E_T_ = ''
                  AND D1.D1_FILIAL = ? AND D1.D1_COD = ?
                  AND D1.D1_DTDIGIT BETWEEN ? AND ?
                  AND {return_eligibility}
                GROUP BY SUBSTRING(D1.D1_DTDIGIT, 1, 6), D1.D1_FORNECE, D1.D1_LOJA
            ) movements
            GROUP BY movements.month, movements.customer_code, movements.customer_store
            ORDER BY movements.month, movements.customer_code, movements.customer_store
        """
        sales_params = (
            branch, product_code, begin_date, end_date, begin_date, end_date,
            branch, product_code, begin_date, end_date,
        )
        with self as repo:
            product = repo.execute_one(product_sql, (product_code, branch, branch))
            if not product:
                return None
            rows = repo.execute_query(sql, sales_params)

        analytics = summarize_product_sales(rows, months=months, today=today)
        return {
            "branch": branch,
            "product": product,
            **analytics,
            "source": "TOTVS Protheus: SD2 (notas de saída) menos SD1 (devoluções de vendas), critérios fiscais ROL",
        }
