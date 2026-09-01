# app/infrastructure/persistence/totvs/financial_repositories/financial_repository.py
from app.application.dto.financial.get_rol_request import GetRolRequest
from app.application.services.financial.financial_rol_cache import (
    financial_rol_cache_key,
    get_cached_financial_rol,
    set_cached_financial_rol,
)
from app.domain.ports.financial.financial_query_repository_port import FinancialQueryRepositoryPort
from app.domain.services.commercial_analysis_filter_service import (
    CommercialAnalysisFilterService,
)
from app.domain.services.commercial.commercial_rol_return_sql import (
    CommercialRolReturnSql,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder


class FinancialRepository(BaseRepository, FinancialQueryRepositoryPort):

    def get_rol(self, request: GetRolRequest) -> dict:
        cache_key = financial_rol_cache_key(request)
        cached = get_cached_financial_rol(cache_key)
        if cached is not None:
            return cached

        result = self._load_rol(request)
        set_cached_financial_rol(cache_key, result)
        return result

    def list_rol_invoices(self, request: GetRolRequest, *, limit: int) -> list[dict]:
        vendas_where, vendas_params, exists_where, exists_params, dev_where, dev_params = (
            self._rol_filter_clauses(request)
        )
        fetch_limit = max(1, int(limit)) + 1
        sale_gross = CommercialRolReturnSql.sale_gross_sum_expr(d2_alias="D2")
        sale_net = CommercialRolReturnSql.sale_net_sum_expr(d2_alias="D2")
        return_net = CommercialRolReturnSql.return_net_sum_expr(d1_alias="D1")
        eligibility = CommercialRolReturnSql.sale_eligibility_predicate(
            exists_where=exists_where
        )
        sql = f"""
        SELECT TOP (?)
            kind,
            branch,
            issue_date,
            invoice_number,
            series,
            customer_code,
            customer_store,
            customer_name,
            gross,
            discounts,
            returns,
            taxes,
            rol
        FROM (
            SELECT
                'sale' AS kind,
                RTRIM(D2.D2_FILIAL) AS branch,
                MIN(D2.D2_EMISSAO) AS issue_date,
                RTRIM(D2.D2_DOC) AS invoice_number,
                RTRIM(D2.D2_SERIE) AS series,
                RTRIM(D2.D2_CLIENTE) AS customer_code,
                RTRIM(D2.D2_LOJA) AS customer_store,
                MAX(RTRIM(ISNULL(A1.A1_NOME, ''))) AS customer_name,
                {sale_gross} AS gross,
                SUM(CONVERT(FLOAT, ISNULL(D2.D2_DESCON, 0) + ISNULL(D2.D2_DESC, 0))) AS discounts,
                CONVERT(FLOAT, 0) AS returns,
                SUM(CONVERT(FLOAT,
                    ISNULL(D2.D2_VALICM, 0)
                    + ISNULL(D2.D2_VALIMP5, 0)
                    + ISNULL(D2.D2_VALIMP6, 0)
                )) AS taxes,
                {sale_net} AS rol
            FROM SD2010 D2 WITH (NOLOCK)
            {CommercialRolReturnSql.sale_customer_join(d2_alias="D2", a1_alias="A1", with_nolock=True)}
            {CommercialRolReturnSql.sale_tes_join(d2_alias="D2", f4_alias="F4", with_nolock=True)}
            WHERE {vendas_where}
                AND {eligibility}
            GROUP BY D2.D2_FILIAL, D2.D2_DOC, D2.D2_SERIE, D2.D2_CLIENTE, D2.D2_LOJA

            UNION ALL

            SELECT
                'return' AS kind,
                RTRIM(D1.D1_FILIAL) AS branch,
                MIN(D1.D1_DTDIGIT) AS issue_date,
                RTRIM(D1.D1_DOC) AS invoice_number,
                RTRIM(D1.D1_SERIE) AS series,
                RTRIM(D1.D1_FORNECE) AS customer_code,
                RTRIM(D1.D1_LOJA) AS customer_store,
                MAX(RTRIM(ISNULL(A1D.A1_NOME, ''))) AS customer_name,
                CONVERT(FLOAT, 0) AS gross,
                CONVERT(FLOAT, 0) AS discounts,
                {return_net} AS returns,
                CONVERT(FLOAT, 0) AS taxes,
                -{return_net} AS rol
            FROM SD1010 D1 WITH (NOLOCK)
            LEFT JOIN SA1010 A1D WITH (NOLOCK)
                ON  A1D.D_E_L_E_T_ = ''
                AND A1D.A1_COD  = D1.D1_FORNECE
                AND A1D.A1_LOJA = D1.D1_LOJA
            {CommercialRolReturnSql.tes_join(d1_alias="D1", f4_alias="F4D", with_nolock=True)}
            WHERE {dev_where}
                AND {CommercialRolReturnSql.sales_return_predicate(d1_alias="D1", f4_alias="F4D")}
            GROUP BY D1.D1_FILIAL, D1.D1_DOC, D1.D1_SERIE, D1.D1_FORNECE, D1.D1_LOJA
        ) AS invoices
        ORDER BY issue_date, branch, invoice_number, series, kind
        """
        params = (fetch_limit,) + vendas_params + exists_params + dev_params
        with self as repo:
            return repo.execute_query(sql, params)

    def _rol_filter_clauses(
        self, request: GetRolRequest
    ) -> tuple[str, tuple, str, tuple, str, tuple]:
        vendas_qb = QueryBuilder()
        vendas_qb.raw("D2.D_E_L_E_T_ = ''")
        if request.branch:
            vendas_qb.eq("D2.D2_FILIAL", request.branch)
        vendas_qb.date_range("D2.D2_EMISSAO", request.start_date, request.end_date)
        CommercialAnalysisFilterService.apply_to_query_builder(
            vendas_qb,
            customer_code_column="D2.D2_CLIENTE",
            customer_name_column="A1.A1_NOME",
            customer_segment=request.customer_segment,
            customer_codes=request.customer_codes,
            customer_names=request.customer_names,
            exclude_customer_codes=request.exclude_customer_codes,
            exclude_customer_names=request.exclude_customer_names,
        )
        vendas_where, vendas_params = vendas_qb.build()

        exists_qb = QueryBuilder()
        exists_qb.date_range("D1X.D1_DTDIGIT", request.start_date, request.end_date)
        exists_where, exists_params = exists_qb.build()

        dev_qb = QueryBuilder()
        dev_qb.raw("D1.D_E_L_E_T_ = ''")
        if request.branch:
            dev_qb.eq("D1.D1_FILIAL", request.branch)
        dev_qb.date_range("D1.D1_DTDIGIT", request.start_date, request.end_date)
        CommercialAnalysisFilterService.apply_to_query_builder(
            dev_qb,
            customer_code_column="D1.D1_FORNECE",
            customer_name_column="A1D.A1_NOME",
            customer_segment=request.customer_segment,
            customer_codes=request.customer_codes,
            customer_names=request.customer_names,
            exclude_customer_codes=request.exclude_customer_codes,
            exclude_customer_names=request.exclude_customer_names,
        )
        dev_where, dev_params = dev_qb.build()
        return (
            vendas_where,
            vendas_params,
            exists_where,
            exists_params,
            dev_where,
            dev_params,
        )

    def _load_rol(self, request: GetRolRequest) -> dict:
        vendas_where, vendas_params, exists_where, exists_params, dev_where, dev_params = (
            self._rol_filter_clauses(request)
        )

        sql = f"""
        WITH VENDAS AS (
            SELECT
                {CommercialRolReturnSql.sale_gross_sum_expr(d2_alias="D2")} AS VALOR_BRUTO_VENDA,

                SUM(CONVERT(FLOAT,
                    ISNULL(D2.D2_DESCON, 0)
                    + ISNULL(D2.D2_DESC, 0)
                )) AS VALOR_DESCONTOS,

                SUM(CONVERT(FLOAT, ISNULL(D2.D2_VALICM, 0)))  AS VALOR_ICMS,
                SUM(CONVERT(FLOAT, ISNULL(D2.D2_VALIMP5, 0))) AS VALOR_PIS,
                SUM(CONVERT(FLOAT, ISNULL(D2.D2_VALIMP6, 0))) AS VALOR_COFINS,

                {CommercialRolReturnSql.sale_net_sum_expr(d2_alias="D2")} AS VLR_VENDA,

                MIN(D2.D2_EMISSAO) AS MIN_EMISSAO,
                MAX(D2.D2_EMISSAO) AS MAX_EMISSAO

            FROM SD2010 D2 WITH (NOLOCK)

            LEFT JOIN SA1010 A1 WITH (NOLOCK)
                ON  A1.D_E_L_E_T_ = ''
                AND A1.A1_COD  = D2.D2_CLIENTE
                AND A1.A1_LOJA = D2.D2_LOJA

            LEFT JOIN SF4010 F4 WITH (NOLOCK)
                ON  F4.D_E_L_E_T_ = ''
                AND F4.F4_CODIGO = D2.D2_TES
                AND (
                        F4.F4_FILIAL = D2.D2_FILIAL
                     OR F4.F4_FILIAL = ''
                     OR F4.F4_FILIAL IS NULL
                )

            WHERE {vendas_where}
                AND ISNULL(A1.A1_NOME, '') <> ''
                AND ISNULL(D2.D2_TIPO, '') <> 'D'

                AND (
                    D2.D2_CF NOT IN ('5911', '6151')
                    OR (
                        D2.D2_FILIAL = '01'
                        AND D2.D2_CF IN ('5911', '6911')
                        AND D2.D2_COD LIKE '90%'
                        AND ISNULL(F4.F4_DUPLIC, '')  = 'N'
                        AND ISNULL(F4.F4_ESTOQUE, '') = 'S'
                        AND D2.D2_UM = 'MI'
                    )
                )

                AND (
                    ISNULL(F4.F4_DUPLIC, '') = 'S'

                    OR (
                        ISNULL(F4.F4_DUPLIC, '')  = 'N'
                        AND ISNULL(F4.F4_ESTOQUE, '') = 'S'
                        AND ISNULL(F4.F4_FINALID, '') = 'BAIXA ESTOQUE'
                        AND D2.D2_CF  = '5927'
                        AND D2.D2_UM  = 'MI'
                        AND EXISTS (
                            SELECT 1
                            FROM SD1010 D1X WITH (NOLOCK)
                            {CommercialRolReturnSql.tes_join(d1_alias="D1X", f4_alias="F4X", with_nolock=True)}
                            WHERE
                                D1X.D_E_L_E_T_ = ''
                                AND D1X.D1_FILIAL  = D2.D2_FILIAL
                                AND D1X.D1_FORNECE = D2.D2_CLIENTE
                                AND D1X.D1_LOJA    = D2.D2_LOJA
                                AND {exists_where}
                                AND {CommercialRolReturnSql.sales_return_predicate(d1_alias="D1X", f4_alias="F4X")}
                        )
                    )

                    OR (
                        D2.D2_FILIAL = '01'
                        AND D2.D2_CF IN ('5911', '6911')
                        AND D2.D2_COD LIKE '90%'
                        AND ISNULL(F4.F4_DUPLIC, '')  = 'N'
                        AND ISNULL(F4.F4_ESTOQUE, '') = 'S'
                        AND D2.D2_UM = 'MI'
                    )
                )
        ),

        DEVOLUCOES AS (
            SELECT
                {CommercialRolReturnSql.return_net_sum_expr(d1_alias="D1")} AS VLR_DEVOLUCAO

            FROM SD1010 D1 WITH (NOLOCK)

            LEFT JOIN SA1010 A1D WITH (NOLOCK)
                ON  A1D.D_E_L_E_T_ = ''
                AND A1D.A1_COD  = D1.D1_FORNECE
                AND A1D.A1_LOJA = D1.D1_LOJA
            {CommercialRolReturnSql.tes_join(d1_alias="D1", f4_alias="F4D", with_nolock=True)}

            WHERE {dev_where}
                AND {CommercialRolReturnSql.sales_return_predicate(d1_alias="D1", f4_alias="F4D")}
        )

        SELECT
            ? AS branch,

            ISNULL(V.MIN_EMISSAO, '') AS start_date,
            ISNULL(V.MAX_EMISSAO, '') AS end_date,

            ISNULL(V.VALOR_BRUTO_VENDA, 0) AS gross_revenue,
            0 AS other_values,
            0 AS items_without_tes,
            ISNULL(D.VLR_DEVOLUCAO, 0) AS returns,
            ISNULL(V.VALOR_DESCONTOS, 0) AS discounts,

            ISNULL(V.VALOR_ICMS, 0)  AS icms,
            0 AS iss,
            ISNULL(V.VALOR_PIS, 0)   AS pis,
            ISNULL(V.VALOR_COFINS, 0) AS cofins,
            0 AS ipi_separated,

            ISNULL(V.VALOR_ICMS, 0)
            + ISNULL(V.VALOR_PIS, 0)
            + ISNULL(V.VALOR_COFINS, 0) AS rol_taxes,

            ISNULL(V.VLR_VENDA, 0)
            - ISNULL(D.VLR_DEVOLUCAO, 0) AS rol,

            0 AS financial_titles,
            0 AS financial_balance

        FROM (SELECT 1 AS _) AS _pivot
        LEFT JOIN VENDAS V ON 1=1
        LEFT JOIN DEVOLUCOES D ON 1=1
        """

        branch_label = request.branch or "consolidated"
        params = vendas_params + exists_params + dev_params + (branch_label,)

        with self as repo:
            result = repo.execute_one(sql, params)

        return result or {
            "branch": branch_label,
            "start_date": request.start_date or "",
            "end_date": request.end_date or "",
            "gross_revenue": 0,
            "other_values": 0,
            "items_without_tes": 0,
            "returns": 0,
            "discounts": 0,
            "icms": 0,
            "iss": 0,
            "pis": 0,
            "cofins": 0,
            "ipi_separated": 0,
            "rol_taxes": 0,
            "rol": 0,
            "financial_titles": 0,
            "financial_balance": 0,
        }
