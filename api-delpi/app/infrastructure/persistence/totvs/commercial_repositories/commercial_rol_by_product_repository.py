"""ROL por produto / família — mesma fórmula SD2−SD1 do ROL comercial."""

from __future__ import annotations

from app.application.dto.commercial.get_rol_by_product_request import (
    GetRolByProductRequest,
)
from app.domain.entities.commercial.rol_by_product import (
    RolByProductItem,
    RolByProductResult,
)
from app.domain.ports.commercial.commercial_rol_by_product_repository_port import (
    CommercialRolByProductRepositoryPort,
)
from app.domain.services.commercial_analysis_filter_service import (
    CommercialAnalysisFilterService,
)
from app.domain.services.commercial.commercial_rol_return_sql import (
    CommercialRolReturnSql,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder

_NET = CommercialRolReturnSql.sale_net_line_expr(d2_alias="D2")
_GROSS = CommercialRolReturnSql.sale_gross_line_expr(d2_alias="D2")
_DOMESTIC = CommercialRolReturnSql.is_domestic_market_predicate(d2_alias="D2")
_EXPORT = CommercialRolReturnSql.is_export_market_predicate(d2_alias="D2")


class CommercialRolByProductRepository(
    BaseRepository,
    CommercialRolByProductRepositoryPort,
):
    def get_rol_by_product(
        self,
        request: GetRolByProductRequest,
    ) -> RolByProductResult:
        group_by_product = request.group_by == "product"

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

        if group_by_product:
            sale_key_select = """
                    RTRIM(D2.D2_COD) AS PRODUCT_CODE,
                    RTRIM(LTRIM(ISNULL(SB1.B1_GRUPO, ''))) AS PRODUCT_GROUP,
                    ISNULL(
                        NULLIF(RTRIM(SB1.B1_DESC), ''),
                        RTRIM(D2.D2_COD)
                    ) AS PRODUCT_NAME
            """
            sale_group = (
                "RTRIM(D2.D2_COD), RTRIM(LTRIM(ISNULL(SB1.B1_GRUPO, ''))), "
                "ISNULL(NULLIF(RTRIM(SB1.B1_DESC), ''), RTRIM(D2.D2_COD))"
            )
            ret_key_select = """
                    RTRIM(D1.D1_COD) AS PRODUCT_CODE,
                    RTRIM(LTRIM(ISNULL(SB1D.B1_GRUPO, ''))) AS PRODUCT_GROUP
            """
            ret_group = (
                "RTRIM(D1.D1_COD), RTRIM(LTRIM(ISNULL(SB1D.B1_GRUPO, '')))"
            )
            join_ret = "D.PRODUCT_CODE = V.PRODUCT_CODE AND D.PRODUCT_GROUP = V.PRODUCT_GROUP"
            agg_group = "PRODUCT_CODE, PRODUCT_GROUP, PRODUCT_NAME"
            rank_order = "ROL_ITEM DESC, PRODUCT_CODE ASC"
        else:
            sale_key_select = """
                    '' AS PRODUCT_CODE,
                    RTRIM(LTRIM(ISNULL(SB1.B1_GRUPO, ''))) AS PRODUCT_GROUP,
                    RTRIM(LTRIM(ISNULL(SB1.B1_GRUPO, ''))) AS PRODUCT_NAME
            """
            sale_group = "RTRIM(LTRIM(ISNULL(SB1.B1_GRUPO, '')))"
            ret_key_select = """
                    '' AS PRODUCT_CODE,
                    RTRIM(LTRIM(ISNULL(SB1D.B1_GRUPO, ''))) AS PRODUCT_GROUP
            """
            ret_group = "RTRIM(LTRIM(ISNULL(SB1D.B1_GRUPO, '')))"
            join_ret = "D.PRODUCT_GROUP = V.PRODUCT_GROUP"
            agg_group = "PRODUCT_CODE, PRODUCT_GROUP, PRODUCT_NAME"
            rank_order = "ROL_ITEM DESC, PRODUCT_GROUP ASC"

        sql = f"""
            WITH VENDAS AS (
                SELECT
                    {sale_key_select},
                    SUM(CASE WHEN {_DOMESTIC} THEN CONVERT(FLOAT, {_NET}) ELSE 0 END)
                        AS NET_DOMESTIC,
                    SUM(CASE WHEN {_EXPORT} THEN CONVERT(FLOAT, {_NET}) ELSE 0 END)
                        AS NET_EXPORT,
                    SUM(CONVERT(FLOAT, {_NET})) AS NET_TOTAL,
                    SUM(CASE WHEN {_DOMESTIC} THEN CONVERT(FLOAT, {_GROSS}) ELSE 0 END)
                        AS GROSS_DOMESTIC,
                    SUM(CASE WHEN {_EXPORT} THEN CONVERT(FLOAT, {_GROSS}) ELSE 0 END)
                        AS GROSS_EXPORT,
                    SUM(CONVERT(FLOAT, {_GROSS})) AS GROSS_TOTAL
                FROM SD2010 D2 WITH (NOLOCK)
                LEFT JOIN SA1010 A1 WITH (NOLOCK)
                    ON  A1.D_E_L_E_T_ = ''
                    AND A1.A1_COD  = D2.D2_CLIENTE
                    AND A1.A1_LOJA = D2.D2_LOJA
                LEFT JOIN SB1010 SB1 WITH (NOLOCK)
                    ON  SB1.D_E_L_E_T_ = ''
                    AND SB1.B1_COD = D2.D2_COD
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
                GROUP BY {sale_group}
            ),
            DEVOLUCOES AS (
                SELECT
                    {ret_key_select},
                    {CommercialRolReturnSql.return_net_sum_expr(d1_alias="D1")} AS VLR_DEVOLUCAO
                FROM SD1010 D1 WITH (NOLOCK)
                LEFT JOIN SA1010 A1D WITH (NOLOCK)
                    ON  A1D.D_E_L_E_T_ = ''
                    AND A1D.A1_COD  = D1.D1_FORNECE
                    AND A1D.A1_LOJA = D1.D1_LOJA
                LEFT JOIN SB1010 SB1D WITH (NOLOCK)
                    ON  SB1D.D_E_L_E_T_ = ''
                    AND SB1D.B1_COD = D1.D1_COD
                {CommercialRolReturnSql.tes_join(d1_alias="D1", f4_alias="F4D", with_nolock=True)}
                WHERE {dev_where}
                    AND {CommercialRolReturnSql.sales_return_predicate(d1_alias="D1", f4_alias="F4D")}
                GROUP BY {ret_group}
            ),
            ROL_ITEM AS (
                SELECT
                    ISNULL(V.PRODUCT_CODE, D.PRODUCT_CODE) AS PRODUCT_CODE,
                    ISNULL(V.PRODUCT_GROUP, D.PRODUCT_GROUP) AS PRODUCT_GROUP,
                    ISNULL(V.PRODUCT_NAME, ISNULL(V.PRODUCT_GROUP, D.PRODUCT_GROUP))
                        AS PRODUCT_NAME,
                    ISNULL(V.NET_DOMESTIC, 0) AS DOMESTIC_ROL,
                    ISNULL(V.NET_EXPORT, 0) AS EXPORT_ROL,
                    ISNULL(V.NET_TOTAL, 0) - ISNULL(D.VLR_DEVOLUCAO, 0) AS ROL_ITEM,
                    ISNULL(V.GROSS_DOMESTIC, 0) AS DOMESTIC_GROSS,
                    ISNULL(V.GROSS_EXPORT, 0) AS EXPORT_GROSS,
                    ISNULL(V.GROSS_TOTAL, 0) AS GROSS_ITEM
                FROM VENDAS V
                FULL OUTER JOIN DEVOLUCOES D
                    ON {join_ret}
            ),
            ROL_FILTRADO AS (
                SELECT *
                FROM ROL_ITEM
                WHERE ROL_ITEM <> 0 OR GROSS_ITEM <> 0
                   OR DOMESTIC_ROL <> 0 OR EXPORT_ROL <> 0
            ),
            TOTAIS AS (
                SELECT
                    ISNULL(SUM(ROL_ITEM), 0) AS TOTAL_ROL,
                    ISNULL(SUM(GROSS_ITEM), 0) AS TOTAL_GROSS,
                    COUNT(1) AS ITEMS_COUNT
                FROM ROL_FILTRADO
            ),
            RANKED AS (
                SELECT
                    RF.*,
                    T.TOTAL_ROL,
                    T.TOTAL_GROSS,
                    T.ITEMS_COUNT,
                    ROW_NUMBER() OVER (ORDER BY {rank_order}) AS RNK
                FROM ROL_FILTRADO RF
                CROSS JOIN TOTAIS T
            )
            SELECT
                PRODUCT_CODE,
                PRODUCT_GROUP,
                PRODUCT_NAME,
                DOMESTIC_ROL,
                EXPORT_ROL,
                ROL_ITEM,
                DOMESTIC_GROSS,
                EXPORT_GROSS,
                GROSS_ITEM,
                TOTAL_ROL,
                TOTAL_GROSS,
                ITEMS_COUNT,
                RNK
            FROM RANKED
            ORDER BY RNK
        """

        countries_sql = f"""
            SELECT DISTINCT
                RTRIM(ISNULL(A1.A1_PAIS, '')) AS PAIS
            FROM SD2010 D2 WITH (NOLOCK)
            LEFT JOIN SA1010 A1 WITH (NOLOCK)
                ON  A1.D_E_L_E_T_ = ''
                AND A1.A1_COD  = D2.D2_CLIENTE
                AND A1.A1_LOJA = D2.D2_LOJA
            LEFT JOIN SB1010 SB1 WITH (NOLOCK)
                ON  SB1.D_E_L_E_T_ = ''
                AND SB1.B1_COD = D2.D2_COD
            LEFT JOIN SF4010 F4 WITH (NOLOCK)
                ON  F4.D_E_L_E_T_ = ''
                AND F4.F4_CODIGO = D2.D2_TES
                AND (
                        F4.F4_FILIAL = D2.D2_FILIAL
                     OR F4.F4_FILIAL = ''
                     OR F4.F4_FILIAL IS NULL
                )
            WHERE {vendas_where}
                AND {_EXPORT}
                AND ISNULL(A1.A1_NOME, '') <> ''
                AND ISNULL(D2.D2_TIPO, '') <> 'D'
                AND ISNULL(A1.A1_PAIS, '') <> ''
                AND (
                    ISNULL(F4.F4_DUPLIC, '') = 'S'
                    OR (
                        ISNULL(F4.F4_DUPLIC, '')  = 'N'
                        AND ISNULL(F4.F4_ESTOQUE, '') = 'S'
                        AND ISNULL(F4.F4_FINALID, '') = 'BAIXA ESTOQUE'
                        AND D2.D2_CF  = '5927'
                        AND D2.D2_UM  = 'MI'
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
            ORDER BY PAIS
        """

        params = vendas_params + exists_params + dev_params
        with self as repo:
            rows = repo.execute_query(sql, params) or []
            country_rows = repo.execute_query(
                countries_sql, vendas_params
            ) or []

        branch_label = request.branch or "consolidated"
        countries = tuple(
            str(row.get("PAIS") or "").strip()
            for row in country_rows
            if str(row.get("PAIS") or "").strip()
        )

        if not rows:
            return RolByProductResult(
                branch=branch_label,
                start_date=str(request.start_date or ""),
                end_date=str(request.end_date or ""),
                group_by=request.group_by,
                market=request.market,
                items=(),
                export_destination_countries=countries,
                total_rol=0.0,
                total_gross_revenue=0.0,
                items_count=0,
            )

        total_rol = float(rows[0].get("TOTAL_ROL") or 0)
        total_gross = float(rows[0].get("TOTAL_GROSS") or 0)
        items_count = int(rows[0].get("ITEMS_COUNT") or 0)
        limit = int(request.limit)
        top_rows = rows[:limit]

        def _share(value: float) -> float | None:
            if total_rol == 0:
                return None
            return round((value * 100.0) / total_rol, 2)

        items = tuple(
            RolByProductItem(
                product_code=str(row.get("PRODUCT_CODE") or "").strip(),
                product_group=str(row.get("PRODUCT_GROUP") or "").strip(),
                product_name=str(row.get("PRODUCT_NAME") or "").strip(),
                domestic_rol=float(row.get("DOMESTIC_ROL") or 0),
                export_rol=float(row.get("EXPORT_ROL") or 0),
                rol=float(row.get("ROL_ITEM") or 0),
                domestic_gross_revenue=float(row.get("DOMESTIC_GROSS") or 0),
                export_gross_revenue=float(row.get("EXPORT_GROSS") or 0),
                gross_revenue=float(row.get("GROSS_ITEM") or 0),
                share_pct=_share(float(row.get("ROL_ITEM") or 0)),
                rank=int(row.get("RNK") or 0),
            )
            for row in top_rows
        )

        return RolByProductResult(
            branch=branch_label,
            start_date=str(request.start_date or ""),
            end_date=str(request.end_date or ""),
            group_by=request.group_by,
            market=request.market,
            items=items,
            export_destination_countries=countries,
            total_rol=total_rol,
            total_gross_revenue=total_gross,
            items_count=items_count,
        )
