"""ROL por centro do cliente — mesma fórmula SD2−SD1 do ROL comercial.

Classificação pelo cadastro **atual** SA7/ZC0 (não há snapshot na NF).
"""

from __future__ import annotations

from app.application.dto.commercial.get_rol_by_customer_center_request import (
    GROUP_BY_CENTER_PRODUCT,
    GetRolByCustomerCenterRequest,
)
from app.domain.entities.commercial.rol_by_customer_center import (
    RolByCustomerCenterItem,
    RolByCustomerCenterResult,
)
from app.domain.ports.commercial.commercial_rol_by_customer_center_repository_port import (
    CommercialRolByCustomerCenterRepositoryPort,
)
from app.domain.services.commercial.commercial_rol_return_sql import (
    CommercialRolReturnSql,
)
from app.domain.services.commercial_analysis_filter_service import (
    CommercialAnalysisFilterService,
)
from app.domain.totvs.protheus_customer_center import (
    UNCLASSIFIED_CUSTOMER_CENTER_NAME,
    customer_center_active_expr,
    customer_center_classification_join_sql,
    customer_center_code_expr,
    customer_center_filter_column,
    customer_center_master_join_sql,
    customer_center_name_expr,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder

_NET = CommercialRolReturnSql.sale_net_line_expr(d2_alias="D2")
_GROSS = CommercialRolReturnSql.sale_gross_line_expr(d2_alias="D2")
_CENTER_CODE = customer_center_code_expr()
_CENTER_NAME = customer_center_name_expr()
_CENTER_ACTIVE = customer_center_active_expr()


class CommercialRolByCustomerCenterRepository(
    BaseRepository,
    CommercialRolByCustomerCenterRepositoryPort,
):
    def get_rol_by_customer_center(
        self,
        request: GetRolByCustomerCenterRequest,
    ) -> RolByCustomerCenterResult:
        detail = request.group_by == GROUP_BY_CENTER_PRODUCT

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
            customer_center_column=customer_center_filter_column(
                request.customer_centers
            ),
            customer_centers=request.customer_centers,
            exclude_customer_codes=request.exclude_customer_codes,
            exclude_customer_names=request.exclude_customer_names,
        )
        if request.customer_stores:
            vendas_qb.in_list("D2.D2_LOJA", request.customer_stores)
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
            customer_center_column=customer_center_filter_column(
                request.customer_centers
            ),
            customer_centers=request.customer_centers,
            exclude_customer_codes=request.exclude_customer_codes,
            exclude_customer_names=request.exclude_customer_names,
        )
        if request.customer_stores:
            dev_qb.in_list("D1.D1_LOJA", request.customer_stores)
        if request.product_codes:
            dev_qb.in_list("D1.D1_COD", request.product_codes)
        if request.product_groups:
            dev_qb.in_list("RTRIM(LTRIM(SB1D.B1_GRUPO))", request.product_groups)
        dev_where, dev_params = dev_qb.build()

        sale_center_join = customer_center_classification_join_sql(
            product_column="D2.D2_COD",
            customer_column="D2.D2_CLIENTE",
            store_column="D2.D2_LOJA",
        )
        sale_master_join = customer_center_master_join_sql()
        return_center_join = customer_center_classification_join_sql(
            product_column="D1.D1_COD",
            customer_column="D1.D1_FORNECE",
            store_column="D1.D1_LOJA",
        )
        return_master_join = customer_center_master_join_sql()

        eligibility = CommercialRolReturnSql.sale_eligibility_predicate(
            d2_alias="D2",
            f4_alias="F4",
            a1_alias="A1",
            exists_where=exists_where,
        )

        if detail:
            sale_product_select = """
                    RTRIM(D2.D2_COD) AS PRODUCT_CODE,
                    ISNULL(
                        NULLIF(RTRIM(SB1.B1_DESC), ''),
                        RTRIM(D2.D2_COD)
                    ) AS PRODUCT_NAME
            """
            sale_product_group = (
                "RTRIM(D2.D2_COD), "
                "ISNULL(NULLIF(RTRIM(SB1.B1_DESC), ''), RTRIM(D2.D2_COD))"
            )
            ret_product_select = """
                    RTRIM(D1.D1_COD) AS PRODUCT_CODE,
                    ISNULL(
                        NULLIF(RTRIM(SB1D.B1_DESC), ''),
                        RTRIM(D1.D1_COD)
                    ) AS PRODUCT_NAME
            """
            ret_product_group = (
                "RTRIM(D1.D1_COD), "
                "ISNULL(NULLIF(RTRIM(SB1D.B1_DESC), ''), RTRIM(D1.D1_COD))"
            )
            join_ret = """
                    ISNULL(V.CUSTOMER_CODE, '') = ISNULL(D.CUSTOMER_CODE, '')
                AND ISNULL(V.CUSTOMER_STORE, '') = ISNULL(D.CUSTOMER_STORE, '')
                AND ISNULL(V.CUSTOMER_CENTER, '') = ISNULL(D.CUSTOMER_CENTER, '')
                AND ISNULL(V.PRODUCT_CODE, '') = ISNULL(D.PRODUCT_CODE, '')
            """
        else:
            sale_product_select = """
                    '' AS PRODUCT_CODE,
                    '' AS PRODUCT_NAME
            """
            sale_product_group = ""
            ret_product_select = """
                    '' AS PRODUCT_CODE,
                    '' AS PRODUCT_NAME
            """
            ret_product_group = ""
            join_ret = """
                    ISNULL(V.CUSTOMER_CODE, '') = ISNULL(D.CUSTOMER_CODE, '')
                AND ISNULL(V.CUSTOMER_STORE, '') = ISNULL(D.CUSTOMER_STORE, '')
                AND ISNULL(V.CUSTOMER_CENTER, '') = ISNULL(D.CUSTOMER_CENTER, '')
            """

        sale_group = ", ".join(
            part
            for part in (
                "RTRIM(D2.D2_CLIENTE)",
                "RTRIM(D2.D2_LOJA)",
                _CENTER_CODE,
                _CENTER_NAME,
                _CENTER_ACTIVE,
                sale_product_group,
            )
            if part
        )
        ret_group = ", ".join(
            part
            for part in (
                "RTRIM(D1.D1_FORNECE)",
                "RTRIM(D1.D1_LOJA)",
                _CENTER_CODE,
                _CENTER_NAME,
                _CENTER_ACTIVE,
                ret_product_group,
            )
            if part
        )

        sql = f"""
            WITH VENDAS AS (
                SELECT
                    RTRIM(D2.D2_CLIENTE) AS CUSTOMER_CODE,
                    RTRIM(D2.D2_LOJA) AS CUSTOMER_STORE,
                    MAX(RTRIM(ISNULL(A1.A1_NOME, ''))) AS CUSTOMER_NAME,
                    {_CENTER_CODE} AS CUSTOMER_CENTER,
                    {_CENTER_NAME} AS CUSTOMER_CENTER_NAME,
                    {_CENTER_ACTIVE} AS CENTER_ACTIVE,
                    {sale_product_select},
                    SUM(CONVERT(FLOAT, {_NET})) AS NET_TOTAL,
                    SUM(CONVERT(FLOAT, {_GROSS})) AS GROSS_TOTAL,
                    SUM(CONVERT(FLOAT, ISNULL(D2.D2_QUANT, 0))) AS QTY_TOTAL,
                    CASE
                        WHEN COUNT(DISTINCT NULLIF(RTRIM(D2.D2_UM), '')) = 1
                        THEN MAX(NULLIF(RTRIM(D2.D2_UM), ''))
                        ELSE NULL
                    END AS UNIT,
                    CASE
                        WHEN COUNT(DISTINCT NULLIF(RTRIM(D2.D2_UM), '')) > 1 THEN 1
                        ELSE 0
                    END AS MIXED_UNITS
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
                {sale_center_join}
                {sale_master_join}
                WHERE {vendas_where}
                    AND {eligibility}
                GROUP BY {sale_group}
            ),
            DEVOLUCOES AS (
                SELECT
                    RTRIM(D1.D1_FORNECE) AS CUSTOMER_CODE,
                    RTRIM(D1.D1_LOJA) AS CUSTOMER_STORE,
                    MAX(RTRIM(ISNULL(A1D.A1_NOME, ''))) AS CUSTOMER_NAME,
                    {_CENTER_CODE} AS CUSTOMER_CENTER,
                    {_CENTER_NAME} AS CUSTOMER_CENTER_NAME,
                    {_CENTER_ACTIVE} AS CENTER_ACTIVE,
                    {ret_product_select},
                    {CommercialRolReturnSql.return_net_sum_expr(d1_alias="D1")}
                        AS VLR_DEVOLUCAO,
                    SUM(CONVERT(FLOAT, ISNULL(D1.D1_QUANT, 0))) AS QTY_DEVOLUCAO
                FROM SD1010 D1 WITH (NOLOCK)
                LEFT JOIN SA1010 A1D WITH (NOLOCK)
                    ON  A1D.D_E_L_E_T_ = ''
                    AND A1D.A1_COD  = D1.D1_FORNECE
                    AND A1D.A1_LOJA = D1.D1_LOJA
                LEFT JOIN SB1010 SB1D WITH (NOLOCK)
                    ON  SB1D.D_E_L_E_T_ = ''
                    AND SB1D.B1_COD = D1.D1_COD
                {CommercialRolReturnSql.tes_join(d1_alias="D1", f4_alias="F4D", with_nolock=True)}
                {return_center_join}
                {return_master_join}
                WHERE {dev_where}
                    AND {CommercialRolReturnSql.sales_return_predicate(d1_alias="D1", f4_alias="F4D")}
                GROUP BY {ret_group}
            ),
            ROL_ITEM AS (
                SELECT
                    ISNULL(V.CUSTOMER_CODE, D.CUSTOMER_CODE) AS CUSTOMER_CODE,
                    ISNULL(V.CUSTOMER_STORE, D.CUSTOMER_STORE) AS CUSTOMER_STORE,
                    ISNULL(
                        NULLIF(V.CUSTOMER_NAME, ''),
                        ISNULL(D.CUSTOMER_NAME, '')
                    ) AS CUSTOMER_NAME,
                    ISNULL(V.CUSTOMER_CENTER, D.CUSTOMER_CENTER) AS CUSTOMER_CENTER,
                    ISNULL(
                        V.CUSTOMER_CENTER_NAME,
                        ISNULL(D.CUSTOMER_CENTER_NAME, '{UNCLASSIFIED_CUSTOMER_CENTER_NAME}')
                    ) AS CUSTOMER_CENTER_NAME,
                    COALESCE(V.CENTER_ACTIVE, D.CENTER_ACTIVE) AS CENTER_ACTIVE,
                    ISNULL(V.PRODUCT_CODE, D.PRODUCT_CODE) AS PRODUCT_CODE,
                    ISNULL(V.PRODUCT_NAME, D.PRODUCT_NAME) AS PRODUCT_NAME,
                    ISNULL(V.NET_TOTAL, 0) - ISNULL(D.VLR_DEVOLUCAO, 0) AS ROL_ITEM,
                    ISNULL(V.GROSS_TOTAL, 0) AS GROSS_ITEM,
                    ISNULL(V.QTY_TOTAL, 0) - ISNULL(D.QTY_DEVOLUCAO, 0) AS QTY_ITEM,
                    V.UNIT AS UNIT,
                    ISNULL(V.MIXED_UNITS, 0) AS MIXED_UNITS
                FROM VENDAS V
                FULL OUTER JOIN DEVOLUCOES D
                    ON {join_ret}
            ),
            ROL_FILTRADO AS (
                SELECT *
                FROM ROL_ITEM
                WHERE ROL_ITEM <> 0 OR GROSS_ITEM <> 0 OR QTY_ITEM <> 0
            ),
            TOTAIS AS (
                SELECT
                    ISNULL(SUM(ROL_ITEM), 0) AS TOTAL_ROL,
                    ISNULL(SUM(GROSS_ITEM), 0) AS TOTAL_GROSS,
                    ISNULL(SUM(QTY_ITEM), 0) AS TOTAL_QTY,
                    COUNT(1) AS ITEMS_COUNT,
                    ISNULL(
                        SUM(CASE WHEN CUSTOMER_CENTER IS NULL THEN ROL_ITEM ELSE 0 END),
                        0
                    ) AS UNCLASSIFIED_ROL,
                    ISNULL(
                        SUM(CASE WHEN CUSTOMER_CENTER IS NULL THEN QTY_ITEM ELSE 0 END),
                        0
                    ) AS UNCLASSIFIED_QTY
                FROM ROL_FILTRADO
            ),
            RANKED AS (
                SELECT
                    RF.*,
                    T.TOTAL_ROL,
                    T.TOTAL_GROSS,
                    T.TOTAL_QTY,
                    T.ITEMS_COUNT,
                    T.UNCLASSIFIED_ROL,
                    T.UNCLASSIFIED_QTY,
                    ROW_NUMBER() OVER (
                        ORDER BY
                            RF.ROL_ITEM DESC,
                            RF.CUSTOMER_CODE ASC,
                            RF.CUSTOMER_STORE ASC,
                            ISNULL(RF.CUSTOMER_CENTER, '') ASC,
                            RF.PRODUCT_CODE ASC
                    ) AS RNK
                FROM ROL_FILTRADO RF
                CROSS JOIN TOTAIS T
            )
            SELECT
                CUSTOMER_CODE,
                CUSTOMER_STORE,
                CUSTOMER_NAME,
                CUSTOMER_CENTER,
                CUSTOMER_CENTER_NAME,
                CENTER_ACTIVE,
                PRODUCT_CODE,
                PRODUCT_NAME,
                ROL_ITEM,
                GROSS_ITEM,
                QTY_ITEM,
                UNIT,
                MIXED_UNITS,
                TOTAL_ROL,
                TOTAL_GROSS,
                TOTAL_QTY,
                ITEMS_COUNT,
                UNCLASSIFIED_ROL,
                UNCLASSIFIED_QTY,
                RNK
            FROM RANKED
            ORDER BY RNK
        """

        params = vendas_params + exists_params + dev_params
        with self as repo:
            rows = repo.execute_query(sql, params) or []

        branch_label = request.branch or "consolidated"
        if not rows:
            return RolByCustomerCenterResult(
                branch=branch_label,
                start_date=str(request.start_date or ""),
                end_date=str(request.end_date or ""),
                group_by=request.group_by,
                market=request.market,
                items=(),
                total_rol=0.0,
                total_gross_revenue=0.0,
                total_qty=0.0,
                items_count=0,
                unclassified_rol=0.0,
                unclassified_qty=0.0,
            )

        total_rol = float(rows[0].get("TOTAL_ROL") or 0)
        total_gross = float(rows[0].get("TOTAL_GROSS") or 0)
        total_qty = float(rows[0].get("TOTAL_QTY") or 0)
        items_count = int(rows[0].get("ITEMS_COUNT") or 0)
        unclassified_rol = float(rows[0].get("UNCLASSIFIED_ROL") or 0)
        unclassified_qty = float(rows[0].get("UNCLASSIFIED_QTY") or 0)
        top_rows = rows[: int(request.limit)]

        def _share(value: float) -> float | None:
            if total_rol == 0:
                return None
            return round((value * 100.0) / total_rol, 2)

        def _center_code(row: dict) -> str | None:
            value = str(row.get("CUSTOMER_CENTER") or "").strip()
            return value or None

        def _center_active(row: dict) -> bool | None:
            if _center_code(row) is None:
                return None
            raw = row.get("CENTER_ACTIVE")
            if raw is None:
                return False
            return bool(int(raw))

        items = tuple(
            RolByCustomerCenterItem(
                customer_code=str(row.get("CUSTOMER_CODE") or "").strip(),
                customer_store=str(row.get("CUSTOMER_STORE") or "").strip(),
                customer_name=str(row.get("CUSTOMER_NAME") or "").strip(),
                customer_center=_center_code(row),
                customer_center_name=(
                    str(row.get("CUSTOMER_CENTER_NAME") or "").strip()
                    or UNCLASSIFIED_CUSTOMER_CENTER_NAME
                ),
                center_active=_center_active(row),
                product_code=str(row.get("PRODUCT_CODE") or "").strip(),
                product_name=str(row.get("PRODUCT_NAME") or "").strip(),
                rol=float(row.get("ROL_ITEM") or 0),
                gross_revenue=float(row.get("GROSS_ITEM") or 0),
                qty=float(row.get("QTY_ITEM") or 0),
                unit=(str(row.get("UNIT") or "").strip() or None),
                mixed_units=bool(int(row.get("MIXED_UNITS") or 0)),
                share_pct=_share(float(row.get("ROL_ITEM") or 0)),
                rank=int(row.get("RNK") or 0),
            )
            for row in top_rows
        )

        return RolByCustomerCenterResult(
            branch=branch_label,
            start_date=str(request.start_date or ""),
            end_date=str(request.end_date or ""),
            group_by=request.group_by,
            market=request.market,
            items=items,
            total_rol=total_rol,
            total_gross_revenue=total_gross,
            total_qty=total_qty,
            items_count=items_count,
            unclassified_rol=unclassified_rol,
            unclassified_qty=unclassified_qty,
        )
