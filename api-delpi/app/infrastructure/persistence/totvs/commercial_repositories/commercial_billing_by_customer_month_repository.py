"""Matriz faturamento cliente × mês — gross NF (F2_VALBRUT) ou net ROL canônico."""

from __future__ import annotations

from typing import Sequence

from app.application.dto.commercial.get_billing_by_customer_month_request import (
    GetBillingByCustomerMonthRequest,
)
from app.domain.ports.commercial.commercial_billing_by_customer_month_repository_port import (
    CommercialBillingByCustomerMonthRepositoryPort,
)
from app.domain.services.commercial.commercial_rol_return_sql import (
    CommercialRolReturnSql,
)
from app.domain.services.commercial_analysis_filter_service import (
    CommercialAnalysisFilterService,
)
from app.domain.totvs.protheus_customer_center import (
    customer_center_filter_column,
    customer_center_join_sql,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder


class CommercialBillingByCustomerMonthRepository(
    BaseRepository,
    CommercialBillingByCustomerMonthRepositoryPort,
):
    def list_billing_rows(
        self,
        request: GetBillingByCustomerMonthRequest,
    ) -> Sequence[dict]:
        if request.nature == "gross":
            sql, params = self._build_gross_sql(request)
        else:
            sql, params = self._build_net_sql(request)
        with self as repo:
            return repo.execute_query(sql, params) or []

    def _sale_filters(
        self,
        request: GetBillingByCustomerMonthRequest,
        *,
        customer_code_column: str,
        customer_name_column: str,
        date_column: str,
    ) -> tuple[str, list]:
        alias = customer_code_column.split(".")[0]
        qb = QueryBuilder()
        qb.raw(f"{alias}.D_E_L_E_T_ = ''")
        if request.branch:
            if alias == "D2":
                qb.eq("D2.D2_FILIAL", request.branch)
            else:
                qb.eq("D1.D1_FILIAL", request.branch)
        qb.date_range(date_column, request.start_date, request.end_date)
        CommercialAnalysisFilterService.apply_to_query_builder(
            qb,
            customer_code_column=customer_code_column,
            customer_name_column=customer_name_column,
            customer_segment=request.customer_segment,
            customer_codes=request.customer_codes,
            customer_names=request.customer_names,
            customer_center_column=customer_center_filter_column(
                request.customer_centers
            ),
            customer_centers=request.customer_centers,
            exclude_customer_codes=request.exclude_customer_codes,
            exclude_customer_names=request.exclude_customer_names,
        )
        return qb.build()

    def _build_gross_sql(
        self,
        request: GetBillingByCustomerMonthRequest,
    ) -> tuple[str, list]:
        where_sql, where_params = self._sale_filters(
            request,
            customer_code_column="D2.D2_CLIENTE",
            customer_name_column="A1.A1_NOME",
            date_column="D2.D2_EMISSAO",
        )
        centers = request.customer_centers
        center_join = customer_center_join_sql(
            centers=centers,
            product_column="D2.D2_COD",
            customer_column="D2.D2_CLIENTE",
            store_column="D2.D2_LOJA",
        )
        sql = f"""
            WITH note_base AS (
                SELECT
                    D2.D2_CLIENTE AS customer_code,
                    D2.D2_LOJA AS customer_store,
                    D2.D2_FILIAL AS branch,
                    D2.D2_DOC AS invoice_number,
                    D2.D2_SERIE AS invoice_series,
                    MAX(D2.D2_EMISSAO) AS issue_date,
                    MAX(CONVERT(FLOAT, ISNULL(F2.F2_VALBRUT, 0))) AS note_value,
                    MAX(ISNULL(F2.F2_TIPO, D2.D2_TIPO)) AS doc_type
                  FROM SD2010 D2 WITH (NOLOCK)
                  INNER JOIN SF2010 F2 WITH (NOLOCK)
                    ON F2.F2_FILIAL = D2.D2_FILIAL
                   AND F2.F2_DOC = D2.D2_DOC
                   AND F2.F2_SERIE = D2.D2_SERIE
                   AND F2.D_E_L_E_T_ = ''
                  {CommercialRolReturnSql.sale_customer_join(with_nolock=True)}
                  {center_join}
                 WHERE {where_sql}
                 GROUP BY
                    D2.D2_CLIENTE,
                    D2.D2_LOJA,
                    D2.D2_FILIAL,
                    D2.D2_DOC,
                    D2.D2_SERIE
            ),
            monthly AS (
                SELECT
                    customer_code,
                    customer_store,
                    LEFT(LTRIM(RTRIM(CONVERT(VARCHAR(8), issue_date))), 6) AS year_month,
                    SUM(
                        CASE
                            WHEN ISNULL(doc_type, '') = 'D' THEN 0
                            ELSE note_value
                        END
                    ) AS billed_value
                  FROM note_base
                 GROUP BY
                    customer_code,
                    customer_store,
                    LEFT(LTRIM(RTRIM(CONVERT(VARCHAR(8), issue_date))), 6)
            )
            SELECT
                M.customer_code,
                M.customer_store,
                ISNULL(
                    NULLIF(RTRIM(SA1.A1_NREDUZ), ''),
                    ISNULL(RTRIM(SA1.A1_NOME), M.customer_code)
                ) AS customer_name,
                M.year_month,
                M.billed_value
              FROM monthly M
              LEFT JOIN SA1010 SA1 WITH (NOLOCK)
                ON  SA1.D_E_L_E_T_ = ''
                AND SA1.A1_COD = M.customer_code
                AND SA1.A1_LOJA = M.customer_store
             WHERE M.billed_value <> 0
             ORDER BY M.customer_code, M.customer_store, M.year_month
        """
        return sql, list(where_params)

    def _build_net_sql(
        self,
        request: GetBillingByCustomerMonthRequest,
    ) -> tuple[str, list]:
        vendas_where, vendas_params = self._sale_filters(
            request,
            customer_code_column="D2.D2_CLIENTE",
            customer_name_column="A1.A1_NOME",
            date_column="D2.D2_EMISSAO",
        )
        exists_qb = QueryBuilder()
        exists_qb.date_range("D1X.D1_DTDIGIT", request.start_date, request.end_date)
        exists_where, exists_params = exists_qb.build()
        dev_where, dev_params = self._sale_filters(
            request,
            customer_code_column="D1.D1_FORNECE",
            customer_name_column="A1D.A1_NOME",
            date_column="D1.D1_DTDIGIT",
        )
        centers = request.customer_centers
        sale_center_join = customer_center_join_sql(
            centers=centers,
            product_column="D2.D2_COD",
            customer_column="D2.D2_CLIENTE",
            store_column="D2.D2_LOJA",
        )
        return_center_join = customer_center_join_sql(
            centers=centers,
            product_column="D1.D1_COD",
            customer_column="D1.D1_FORNECE",
            store_column="D1.D1_LOJA",
        )
        eligibility = CommercialRolReturnSql.sale_eligibility_predicate(
            exists_where=exists_where,
        )
        sale_period = "LEFT(LTRIM(RTRIM(CONVERT(VARCHAR(8), D2.D2_EMISSAO))), 6)"
        ret_period = "LEFT(LTRIM(RTRIM(CONVERT(VARCHAR(8), D1.D1_DTDIGIT))), 6)"
        sql = f"""
            WITH vendas AS (
                SELECT
                    D2.D2_CLIENTE AS customer_code,
                    D2.D2_LOJA AS customer_store,
                    {sale_period} AS year_month,
                    {CommercialRolReturnSql.sale_net_sum_expr(d2_alias="D2")} AS billed_value
                  FROM SD2010 D2 WITH (NOLOCK)
                  {CommercialRolReturnSql.sale_customer_join(with_nolock=True)}
                  {CommercialRolReturnSql.sale_tes_join(with_nolock=True)}
                  {sale_center_join}
                 WHERE {vendas_where}
                   AND {eligibility}
                 GROUP BY D2.D2_CLIENTE, D2.D2_LOJA, {sale_period}
            ),
            devolucoes AS (
                SELECT
                    D1.D1_FORNECE AS customer_code,
                    D1.D1_LOJA AS customer_store,
                    {ret_period} AS year_month,
                    {CommercialRolReturnSql.return_net_sum_expr(d1_alias="D1")} AS billed_value
                  FROM SD1010 D1 WITH (NOLOCK)
                  LEFT JOIN SA1010 A1D WITH (NOLOCK)
                    ON  A1D.D_E_L_E_T_ = ''
                    AND A1D.A1_COD = D1.D1_FORNECE
                    AND A1D.A1_LOJA = D1.D1_LOJA
                  {CommercialRolReturnSql.tes_join(d1_alias="D1", f4_alias="F4D", with_nolock=True)}
                  LEFT JOIN SB1010 SB1D WITH (NOLOCK)
                    ON  SB1D.D_E_L_E_T_ = ''
                    AND SB1D.B1_COD = D1.D1_COD
                    AND (
                            SB1D.B1_FILIAL = D1.D1_FILIAL
                         OR SB1D.B1_FILIAL = ''
                         OR SB1D.B1_FILIAL IS NULL
                    )
                  {return_center_join}
                 WHERE {dev_where}
                   AND {CommercialRolReturnSql.sales_return_predicate(d1_alias="D1", f4_alias="F4D", sb1_alias="SB1D")}
                 GROUP BY D1.D1_FORNECE, D1.D1_LOJA, {ret_period}
            ),
            monthly AS (
                SELECT
                    ISNULL(V.customer_code, D.customer_code) AS customer_code,
                    ISNULL(V.customer_store, D.customer_store) AS customer_store,
                    ISNULL(V.year_month, D.year_month) AS year_month,
                    ISNULL(V.billed_value, 0) - ISNULL(D.billed_value, 0) AS billed_value
                  FROM vendas V
                  FULL OUTER JOIN devolucoes D
                    ON D.customer_code = V.customer_code
                   AND D.customer_store = V.customer_store
                   AND D.year_month = V.year_month
            )
            SELECT
                M.customer_code,
                M.customer_store,
                ISNULL(
                    NULLIF(RTRIM(SA1.A1_NREDUZ), ''),
                    ISNULL(RTRIM(SA1.A1_NOME), M.customer_code)
                ) AS customer_name,
                M.year_month,
                M.billed_value
              FROM monthly M
              LEFT JOIN SA1010 SA1 WITH (NOLOCK)
                ON  SA1.D_E_L_E_T_ = ''
                AND SA1.A1_COD = M.customer_code
                AND SA1.A1_LOJA = M.customer_store
             WHERE M.billed_value <> 0
             ORDER BY M.customer_code, M.customer_store, M.year_month
        """
        params = list(vendas_params) + list(exists_params) + list(dev_params)
        return sql, params
