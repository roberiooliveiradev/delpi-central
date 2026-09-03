"""Ranking ROL por cliente — mesma fórmula SD2−SD1 de FinancialRepository.get_rol."""

from __future__ import annotations

from app.application.dto.commercial.get_rol_by_customer_request import (
    GetRolByCustomerRequest,
)
from app.domain.entities.commercial.rol_by_customer import (
    RolByCustomerItem,
    RolByCustomerResult,
)
from app.domain.ports.commercial.commercial_rol_by_customer_repository_port import (
    CommercialRolByCustomerRepositoryPort,
)
from app.domain.services.commercial_analysis_filter_service import (
    CommercialAnalysisFilterService,
)
from app.domain.services.commercial.commercial_rol_return_sql import (
    CommercialRolReturnSql,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder


class CommercialRolByCustomerRepository(
    BaseRepository,
    CommercialRolByCustomerRepositoryPort,
):
    def get_rol_by_customer(
        self,
        request: GetRolByCustomerRequest,
    ) -> RolByCustomerResult:
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
        if request.product_codes:
            vendas_qb.in_list("D2.D2_COD", request.product_codes)
        if request.product_groups:
            vendas_qb.in_list("RTRIM(LTRIM(SB1.B1_GRUPO))", request.product_groups)
        market_pred = CommercialRolReturnSql.market_filter_predicate(
            request.market, d2_alias="D2"
        )
        if market_pred:
            vendas_qb.raw(market_pred)
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
        if request.product_codes:
            dev_qb.in_list("D1.D1_COD", request.product_codes)
        if request.product_groups:
            dev_qb.in_list("RTRIM(LTRIM(SB1D.B1_GRUPO))", request.product_groups)
        # Returns use inbound CFOP; do not apply market filter on SD1.
        dev_where, dev_params = dev_qb.build()

        needs_sb1 = bool(request.product_groups)
        sb1_join = ""
        if needs_sb1:
            sb1_join = """
                LEFT JOIN SB1010 SB1 WITH (NOLOCK)
                    ON  SB1.D_E_L_E_T_ = ''
                    AND SB1.B1_COD = D2.D2_COD
            """
        sb1d_join = ""
        if needs_sb1:
            sb1d_join = """
                LEFT JOIN SB1010 SB1D WITH (NOLOCK)
                    ON  SB1D.D_E_L_E_T_ = ''
                    AND SB1D.B1_COD = D1.D1_COD
            """

        sql = f"""
            WITH VENDAS AS (
                SELECT
                    D2.D2_FILIAL,
                    D2.D2_CLIENTE,
                    D2.D2_LOJA,
                    {CommercialRolReturnSql.sale_net_sum_expr(d2_alias="D2")} AS VLR_VENDA,
                    {CommercialRolReturnSql.sale_gross_sum_expr(d2_alias="D2")} AS VLR_BRUTO
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
                {sb1_join}
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
                GROUP BY D2.D2_FILIAL, D2.D2_CLIENTE, D2.D2_LOJA
            ),
            DEVOLUCOES AS (
                SELECT
                    D1.D1_FILIAL,
                    D1.D1_FORNECE,
                    D1.D1_LOJA,
                    {CommercialRolReturnSql.return_net_sum_expr(d1_alias="D1")} AS VLR_DEVOLUCAO
                FROM SD1010 D1 WITH (NOLOCK)
                LEFT JOIN SA1010 A1D WITH (NOLOCK)
                    ON  A1D.D_E_L_E_T_ = ''
                    AND A1D.A1_COD  = D1.D1_FORNECE
                    AND A1D.A1_LOJA = D1.D1_LOJA
                {CommercialRolReturnSql.tes_join(d1_alias="D1", f4_alias="F4D", with_nolock=True)}
                {sb1d_join}
                WHERE {dev_where}
                    AND {CommercialRolReturnSql.sales_return_predicate(d1_alias="D1", f4_alias="F4D")}
                GROUP BY D1.D1_FILIAL, D1.D1_FORNECE, D1.D1_LOJA
            ),
            ROL_POR_CLIENTE AS (
                SELECT
                    RTRIM(ISNULL(V.D2_CLIENTE, D.D1_FORNECE)) AS COD_CLIENTE,
                    RTRIM(ISNULL(V.D2_LOJA, D.D1_LOJA)) AS LOJA,
                    ISNULL(V.VLR_VENDA, 0) - ISNULL(D.VLR_DEVOLUCAO, 0) AS ROL_CLIENTE,
                    ISNULL(V.VLR_BRUTO, 0) AS GROSS_CLIENTE
                FROM VENDAS V
                FULL OUTER JOIN DEVOLUCOES D
                    ON  D.D1_FILIAL  = V.D2_FILIAL
                    AND D.D1_FORNECE = V.D2_CLIENTE
                    AND D.D1_LOJA    = V.D2_LOJA
            ),
            ROL_AGREGADO AS (
                SELECT
                    COD_CLIENTE,
                    LOJA,
                    SUM(ROL_CLIENTE) AS ROL_CLIENTE,
                    SUM(GROSS_CLIENTE) AS GROSS_CLIENTE
                FROM ROL_POR_CLIENTE
                GROUP BY COD_CLIENTE, LOJA
            ),
            ROL_NOMEADO AS (
                SELECT
                    RA.COD_CLIENTE,
                    RA.LOJA,
                    ISNULL(
                        NULLIF(RTRIM(SA1.A1_NREDUZ), ''),
                        ISNULL(RTRIM(SA1.A1_NOME), RA.COD_CLIENTE)
                    ) AS NOME_CLIENTE,
                    NULLIF(RTRIM(ISNULL(SA1.A1_CGC, '')), '') AS CNPJ,
                    NULLIF(RTRIM(ISNULL(SA1.A1_MUN, '')), '') AS CIDADE,
                    NULLIF(RTRIM(ISNULL(SA1.A1_EST, '')), '') AS UF,
                    RA.ROL_CLIENTE,
                    RA.GROSS_CLIENTE
                FROM ROL_AGREGADO RA
                LEFT JOIN SA1010 SA1 WITH (NOLOCK)
                    ON  SA1.D_E_L_E_T_ = ''
                    AND SA1.A1_COD  = RA.COD_CLIENTE
                    AND SA1.A1_LOJA = RA.LOJA
                WHERE RA.ROL_CLIENTE <> 0 OR RA.GROSS_CLIENTE <> 0
            ),
            TOTAIS AS (
                SELECT
                    ISNULL(SUM(ROL_CLIENTE), 0) AS TOTAL_ROL,
                    ISNULL(SUM(GROSS_CLIENTE), 0) AS TOTAL_GROSS,
                    COUNT(1) AS CUSTOMERS_COUNT
                FROM ROL_NOMEADO
            ),
            RANKED AS (
                SELECT
                    RN.COD_CLIENTE,
                    RN.LOJA,
                    RN.NOME_CLIENTE,
                    RN.CNPJ,
                    RN.CIDADE,
                    RN.UF,
                    RN.ROL_CLIENTE,
                    RN.GROSS_CLIENTE,
                    T.TOTAL_ROL,
                    T.TOTAL_GROSS,
                    T.CUSTOMERS_COUNT,
                    ROW_NUMBER() OVER (ORDER BY RN.ROL_CLIENTE DESC, RN.COD_CLIENTE ASC) AS RNK
                FROM ROL_NOMEADO RN
                CROSS JOIN TOTAIS T
            )
            SELECT
                COD_CLIENTE,
                LOJA,
                NOME_CLIENTE,
                CNPJ,
                CIDADE,
                UF,
                ROL_CLIENTE,
                GROSS_CLIENTE,
                TOTAL_ROL,
                TOTAL_GROSS,
                CUSTOMERS_COUNT,
                RNK
            FROM RANKED
            ORDER BY RNK
        """

        params = vendas_params + exists_params + dev_params
        with self as repo:
            rows = repo.execute_query(sql, params) or []

        branch_label = request.branch or "consolidated"
        if not rows:
            return RolByCustomerResult(
                branch=branch_label,
                start_date=str(request.start_date or ""),
                end_date=str(request.end_date or ""),
                items=(),
                others=None,
                total_rol=0.0,
                customers_count=0,
            )

        total_rol = float(rows[0].get("TOTAL_ROL") or 0)
        customers_count = int(rows[0].get("CUSTOMERS_COUNT") or 0)
        limit = int(request.limit)
        top_rows = rows[:limit]
        rest_rows = rows[limit:]

        def _share(value: float) -> float | None:
            if total_rol == 0:
                return None
            return round((value * 100.0) / total_rol, 2)

        def _optional_str(value: object) -> str | None:
            text = str(value or "").strip()
            return text or None

        items = tuple(
            RolByCustomerItem(
                customer_code=str(row.get("COD_CLIENTE") or "").strip(),
                customer_store=str(row.get("LOJA") or "").strip(),
                customer_name=str(row.get("NOME_CLIENTE") or "").strip(),
                cnpj=_optional_str(row.get("CNPJ")),
                city=_optional_str(row.get("CIDADE")),
                state=_optional_str(row.get("UF")),
                rol=float(row.get("ROL_CLIENTE") or 0),
                gross_revenue=float(row.get("GROSS_CLIENTE") or 0),
                share_pct=_share(float(row.get("ROL_CLIENTE") or 0)),
                rank=int(row.get("RNK") or 0),
            )
            for row in top_rows
        )

        others: RolByCustomerItem | None = None
        if request.include_others and rest_rows:
            others_value = sum(float(row.get("ROL_CLIENTE") or 0) for row in rest_rows)
            others_gross = sum(float(row.get("GROSS_CLIENTE") or 0) for row in rest_rows)
            others = RolByCustomerItem(
                customer_code="",
                customer_store="",
                customer_name="Demais",
                cnpj=None,
                city=None,
                state=None,
                rol=others_value,
                gross_revenue=others_gross,
                share_pct=_share(others_value),
                rank=limit + 1,
            )

        return RolByCustomerResult(
            branch=branch_label,
            start_date=str(request.start_date or ""),
            end_date=str(request.end_date or ""),
            items=items,
            others=others,
            total_rol=total_rol,
            customers_count=customers_count,
        )
