"""SQL builders — ruptura de MP no conjunto do PA (BOM + cobertura + OPs mãe)."""

from __future__ import annotations

from app.domain.services.product.product_bom_validity_filter_service import (
    ProductBomValidityFilterService,
)
from app.domain.services.supplies.safety_stock_classification_service import (
    AVAILABLE_BALANCE_WAREHOUSES,
)
from app.domain.totvs.protheus_product_types import PRODUCT_TYPE_RAW_MATERIAL
from app.domain.totvs.protheus_production_orders import (
    mother_order_key_sql,
    order_finished_predicate_sql,
)
from app.infrastructure.persistence.totvs.production_repositories.production_pa_sql_filters import (
    SC2_MOTHER_OP_SEQUENCE_SQL,
)
from app.infrastructure.persistence.totvs.supplies_repositories.safety_stock_sql import (
    branch_filter_and,
)

DEFAULT_BOM_MAX_DEPTH = 8

_BOM_VALIDITY = ProductBomValidityFilterService.validity_filter_sql_for_today()
_BOM_VALIDITY_RECURSIVE = ProductBomValidityFilterService.validity_filter_sql_for_today(
    alias="c"
)
_MOTHER_KEY_SQL = mother_order_key_sql("RTRIM(SD4.D4_OP)")


def product_header_sql() -> str:
    return """
    SELECT
        RTRIM(SB1.B1_COD) AS product_code,
        RTRIM(SB1.B1_DESC) AS product_description,
        RTRIM(SB1.B1_TIPO) AS product_type,
        RTRIM(SB1.B1_UM) AS unit
    FROM SB1010 SB1 WITH (NOLOCK)
    WHERE SB1.D_E_L_E_T_ = ''
      AND LTRIM(RTRIM(SB1.B1_COD)) = ?
    """


def raw_material_bom_sql() -> str:
    """Explosão SG1 vigente, só componentes ``B1_TIPO = MP``."""
    return f"""
    WITH recursive_bom AS (
        SELECT
            G1_COD AS parent_code,
            G1_COMP AS component_code,
            G1_QUANT AS quantity,
            1 AS bom_level
        FROM SG1010
        WHERE D_E_L_E_T_ = ''
          AND LTRIM(RTRIM(G1_COD)) = ?
          {_BOM_VALIDITY}

        UNION ALL

        SELECT
            c.G1_COD,
            c.G1_COMP,
            c.G1_QUANT,
            p.bom_level + 1
        FROM SG1010 c
        INNER JOIN recursive_bom p
            ON p.component_code = c.G1_COD
        WHERE c.D_E_L_E_T_ = ''
          AND p.bom_level < ?
          {_BOM_VALIDITY_RECURSIVE}
    )
    SELECT
        RTRIM(rb.component_code) AS product_code,
        RTRIM(COALESCE(comp.B1_DESC, '')) AS product_description,
        RTRIM(COALESCE(comp.B1_UM, '')) AS unit,
        RTRIM(ISNULL(comp.B1_SEGUM, '')) AS secondary_unit,
        CAST(ISNULL(comp.B1_CONV, 0) AS FLOAT) AS conversion_factor,
        RTRIM(ISNULL(comp.B1_TIPCONV, '')) AS conversion_type,
        MIN(rb.bom_level) AS bom_level,
        SUM(CAST(ISNULL(rb.quantity, 0) AS FLOAT)) AS structure_quantity
    FROM recursive_bom rb
    INNER JOIN SB1010 comp WITH (NOLOCK)
        ON comp.B1_COD = rb.component_code
       AND comp.D_E_L_E_T_ = ''
       AND RTRIM(comp.B1_TIPO) = '{PRODUCT_TYPE_RAW_MATERIAL}'
    GROUP BY
        rb.component_code,
        comp.B1_DESC,
        comp.B1_UM,
        comp.B1_SEGUM,
        comp.B1_CONV,
        comp.B1_TIPCONV
    ORDER BY
        MIN(rb.bom_level) ASC,
        rb.component_code ASC
    """


def open_mother_orders_sql(*, branch: str) -> tuple[str, list]:
    """OPs mãe abertas do PA (sequência 001, saldo > 0)."""
    and_sql, params = branch_filter_and("OP.C2_FILIAL", branch)
    sql = f"""
    SELECT
        RTRIM(OP.C2_FILIAL) AS branch,
        RTRIM(OP.C2_OP) AS production_order,
        RTRIM(OP.C2_NUM) AS order_number,
        RTRIM(OP.C2_ITEM) AS order_item,
        RTRIM(OP.C2_PRODUTO) AS product_code,
        RTRIM(COALESCE(P.B1_DESC, '')) AS product_description,
        RTRIM(COALESCE(OP.C2_DATPRI, '')) AS planned_start_date,
        RTRIM(COALESCE(OP.C2_DATPRF, '')) AS due_date,
        CAST(ISNULL(OP.C2_QUANT, 0) AS FLOAT) AS planned_quantity,
        CAST(ISNULL(OP.C2_QUJE, 0) AS FLOAT) AS produced_quantity,
        CAST(
            CASE
                WHEN OP.C2_QUANT > OP.C2_QUJE
                THEN OP.C2_QUANT - OP.C2_QUJE
                ELSE 0
            END AS FLOAT
        ) AS open_quantity,
        RTRIM(COALESCE(OP.C2_OBS, '')) AS observation
    FROM SC2010 OP WITH (NOLOCK)
    LEFT JOIN SB1010 P WITH (NOLOCK)
        ON P.B1_COD = OP.C2_PRODUTO
       AND P.D_E_L_E_T_ = ''
    WHERE OP.D_E_L_E_T_ = ''
      AND LTRIM(RTRIM(OP.C2_PRODUTO)) = ?
      AND {SC2_MOTHER_OP_SEQUENCE_SQL}
      AND OP.C2_QUANT > OP.C2_QUJE
      AND NOT {order_finished_predicate_sql("OP.C2_DATRF")}
      {and_sql}
    ORDER BY
        CASE WHEN RTRIM(COALESCE(OP.C2_DATPRI, '')) = '' THEN 1 ELSE 0 END,
        OP.C2_DATPRI ASC,
        OP.C2_OP ASC
    """
    return sql, params


def _product_in_clause(column: str, placeholders: str) -> str:
    return f"AND {column} IN ({placeholders})"


def mp_stock_batch_sql(*, branch: str, product_codes: list[str]) -> tuple[str, list]:
    """Saldo 01+98+99 e ESTSEG das MPs da BOM."""
    placeholders = placeholders_for(product_codes)
    locals_sql = ", ".join(f"'{code}'" for code in AVAILABLE_BALANCE_WAREHOUSES)
    stock_and_sql, stock_params = branch_filter_and("SB2.B2_FILIAL", branch)
    sbz_and_sql, sbz_params = branch_filter_and("S.BZ_FILIAL", branch)
    sql = f"""
    WITH stock_agg AS (
        SELECT
            RTRIM(SB2.B2_COD) AS product_code,
            SUM(
                CASE WHEN RTRIM(SB2.B2_LOCAL) IN ({locals_sql})
                THEN CAST(ISNULL(SB2.B2_QATU, 0) AS FLOAT) ELSE 0 END
            ) AS available_stock
        FROM SB2010 SB2 WITH (NOLOCK)
        WHERE SB2.D_E_L_E_T_ = ''
          {_product_in_clause("SB2.B2_COD", placeholders)}
          {stock_and_sql}
        GROUP BY SB2.B2_COD
    ),
    sbz_agg AS (
        SELECT
            RTRIM(S.BZ_COD) AS product_code,
            SUM(CAST(ISNULL(S.BZ_ESTSEG, 0) AS FLOAT)) AS safety_stock
        FROM SBZ010 S WITH (NOLOCK)
        WHERE S.D_E_L_E_T_ = ''
          AND RTRIM(S.BZ_FILIAL) <> ''
          {_product_in_clause("S.BZ_COD", placeholders)}
          {sbz_and_sql}
        GROUP BY S.BZ_COD
    )
    SELECT
        RTRIM(SB1.B1_COD) AS product_code,
        RTRIM(COALESCE(SB1.B1_DESC, '')) AS product_description,
        RTRIM(ISNULL(SB1.B1_UM, '')) AS unit,
        RTRIM(ISNULL(SB1.B1_SEGUM, '')) AS secondary_unit,
        CAST(ISNULL(SB1.B1_CONV, 0) AS FLOAT) AS conversion_factor,
        RTRIM(ISNULL(SB1.B1_TIPCONV, '')) AS conversion_type,
        ISNULL(st.available_stock, 0) AS available_stock,
        ISNULL(sz.safety_stock, 0) AS safety_stock
    FROM SB1010 SB1 WITH (NOLOCK)
    LEFT JOIN stock_agg st
        ON st.product_code = RTRIM(SB1.B1_COD)
    LEFT JOIN sbz_agg sz
        ON sz.product_code = RTRIM(SB1.B1_COD)
    WHERE SB1.D_E_L_E_T_ = ''
      {_product_in_clause("SB1.B1_COD", placeholders)}
    ORDER BY SB1.B1_COD ASC
    """
    return sql, [*product_codes, *stock_params, *product_codes, *sbz_params, *product_codes]


def open_purchase_orders_batch_sql(*, branch: str, placeholders: str) -> tuple[str, list]:
    """Pedidos SC7 abertos das MPs da BOM (elegibilidade de armazém no Python)."""
    and_sql, params = branch_filter_and("SC7.C7_FILIAL", branch)
    sql = f"""
    SELECT
        RTRIM(SC7.C7_FILIAL) AS branch,
        RTRIM(SC7.C7_NUM) AS order_number,
        RTRIM(SC7.C7_ITEM) AS order_item,
        RTRIM(SC7.C7_PRODUTO) AS product_code,
        RTRIM(COALESCE(SB1.B1_DESC, SC7.C7_DESCRI, '')) AS product_description,
        RTRIM(SC7.C7_LOCAL) AS warehouse,
        RTRIM(SC7.C7_UM) AS unit,
        CAST(
            CASE
                WHEN SC7.C7_QUANT > SC7.C7_QUJE
                THEN SC7.C7_QUANT - SC7.C7_QUJE
                ELSE 0
            END AS FLOAT
        ) AS open_quantity,
        RTRIM(SC7.C7_DATPRF) AS expected_delivery_date,
        RTRIM(COALESCE(SA2.A2_NREDUZ, SA2.A2_NOME, '')) AS supplier_name
    FROM SC7010 SC7 WITH (NOLOCK)
    LEFT JOIN SB1010 SB1 WITH (NOLOCK)
        ON SB1.B1_COD = SC7.C7_PRODUTO
       AND SB1.D_E_L_E_T_ = ''
    LEFT JOIN SA2010 SA2 WITH (NOLOCK)
        ON SA2.A2_COD = SC7.C7_FORNECE
       AND SA2.A2_LOJA = SC7.C7_LOJA
       AND SA2.D_E_L_E_T_ = ''
    WHERE SC7.D_E_L_E_T_ = ''
      AND ISNULL(SC7.C7_RESIDUO, '') <> 'S'
      AND SC7.C7_QUANT > SC7.C7_QUJE
      {_product_in_clause("SC7.C7_PRODUTO", placeholders)}
      {and_sql}
    ORDER BY
        CASE WHEN RTRIM(SC7.C7_DATPRF) = '' THEN 1 ELSE 0 END,
        SC7.C7_DATPRF ASC,
        SC7.C7_NUM ASC,
        SC7.C7_ITEM ASC
    """
    return sql, params


def open_commitments_batch_sql(*, branch: str, placeholders: str) -> tuple[str, list]:
    """Empenhos SD4 abertos das MPs, com OP mãe canônica (LEFT 8 + 001)."""
    and_sql, params = branch_filter_and("SD4.D4_FILIAL", branch)
    sql = f"""
    SELECT
        RTRIM(SD4.D4_FILIAL) AS branch,
        RTRIM(SD4.D4_COD) AS product_code,
        RTRIM(COALESCE(SB1.B1_DESC, '')) AS product_description,
        RTRIM(SD4.D4_LOCAL) AS warehouse,
        RTRIM(SD4.D4_OP) AS production_order,
        RTRIM(COALESCE(EMP.C2_DATPRI, '')) AS commitment_date,
        RTRIM(COALESCE(SB1.B1_UM, '')) AS unit,
        CAST(ISNULL(SD4.D4_QUANT, 0) AS FLOAT) AS open_quantity,
        {_MOTHER_KEY_SQL} AS finished_production_order,
        RTRIM(COALESCE(FP.C2_PRODUTO, '')) AS finished_product_code,
        RTRIM(COALESCE(FP.C2_OBS, '')) AS finished_order_observation
    FROM SD4010 SD4 WITH (NOLOCK)
    LEFT JOIN SB1010 SB1 WITH (NOLOCK)
        ON SB1.B1_COD = SD4.D4_COD
       AND SB1.D_E_L_E_T_ = ''
    LEFT JOIN SC2010 EMP WITH (NOLOCK)
        ON EMP.D_E_L_E_T_ = ''
       AND EMP.C2_FILIAL = SD4.D4_FILIAL
       AND EMP.C2_OP = SD4.D4_OP
    LEFT JOIN SC2010 FP WITH (NOLOCK)
        ON FP.D_E_L_E_T_ = ''
       AND FP.C2_FILIAL = SD4.D4_FILIAL
       AND FP.C2_OP = {_MOTHER_KEY_SQL}
    WHERE SD4.D_E_L_E_T_ = ''
      AND SD4.D4_QUANT > 0
      {_product_in_clause("SD4.D4_COD", placeholders)}
      {and_sql}
    ORDER BY
        CASE WHEN RTRIM(COALESCE(EMP.C2_DATPRI, '')) = '' THEN 1 ELSE 0 END,
        EMP.C2_DATPRI ASC,
        SD4.D4_OP ASC
    """
    return sql, params


def placeholders_for(codes: list[str]) -> str:
    return ", ".join("?" for _ in codes)


