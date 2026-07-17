"""SQL builders — análise de estoque de segurança (MP × SBZ × SB2)."""

from __future__ import annotations

from app.domain.services.supplies.safety_stock_classification_service import (
    AVAILABLE_BALANCE_WAREHOUSES,
    PRIMARY_WAREHOUSE,
    TOLERANCE,
    WORK_IN_PROCESS_WAREHOUSES,
)
from app.domain.services.supplies.safety_stock_supplier_scope_service import (
    INTERNAL_TRANSFER_SUPPLIER_CODES,
    internal_transfer_supplier_codes_sql,
)

__all__ = [
    "AVAILABLE_BALANCE_WAREHOUSES",
    "INTERNAL_TRANSFER_SUPPLIER_CODES",
    "PRIMARY_WAREHOUSE",
    "TOLERANCE",
    "WORK_IN_PROCESS_WAREHOUSES",
    "SORTABLE_COLUMNS",
    "build_where_clauses",
    "linked_suppliers_sql",
    "materials_base_cte",
    "open_commitments_sql",
    "open_purchase_orders_sql",
    "product_detail_sql",
    "resolve_order_by",
    "stock_agg_cte",
]

SORTABLE_COLUMNS: dict[str, str] = {
    "product_code": "product_code",
    "product_description": "product_description",
    "product_group": "product_group",
    "unit": "unit",
    "safety_stock": "safety_stock",
    "primary_stock": "available_stock",
    "work_in_process_stock": "work_in_process_stock",
    "deficit_quantity": "deficit_quantity",
    "status": "status",
}


def _wip_locals_sql() -> str:
    return ", ".join(f"'{code}'" for code in WORK_IN_PROCESS_WAREHOUSES)


def stock_agg_cte(*, branch_param: str = "?") -> str:
    wip = _wip_locals_sql()
    return f"""
    stock_agg AS (
        SELECT
            RTRIM(SB2.B2_COD) AS product_code,
            SUM(
                CASE WHEN RTRIM(SB2.B2_LOCAL) = '{PRIMARY_WAREHOUSE}'
                THEN CAST(ISNULL(SB2.B2_QATU, 0) AS FLOAT) ELSE 0 END
            ) AS primary_stock,
            SUM(
                CASE WHEN RTRIM(SB2.B2_LOCAL) IN ({wip})
                THEN CAST(ISNULL(SB2.B2_QATU, 0) AS FLOAT) ELSE 0 END
            ) AS work_in_process_stock,
            SUM(
                CASE WHEN RTRIM(SB2.B2_LOCAL) = '50'
                THEN CAST(ISNULL(SB2.B2_QATU, 0) AS FLOAT) ELSE 0 END
            ) AS warehouse_50_stock,
            SUM(
                CASE WHEN RTRIM(SB2.B2_LOCAL) = '98'
                THEN CAST(ISNULL(SB2.B2_QATU, 0) AS FLOAT) ELSE 0 END
            ) AS warehouse_98_stock,
            SUM(
                CASE WHEN RTRIM(SB2.B2_LOCAL) = '99'
                THEN CAST(ISNULL(SB2.B2_QATU, 0) AS FLOAT) ELSE 0 END
            ) AS warehouse_99_stock,
            SUM(
                CASE WHEN RTRIM(SB2.B2_LOCAL) IN ({wip})
                THEN CAST(ISNULL(SB2.B2_QEMP, 0) AS FLOAT) ELSE 0 END
            ) AS work_in_process_committed,
            SUM(
                CASE WHEN RTRIM(SB2.B2_LOCAL) IN ({wip})
                THEN CAST(
                    ISNULL(SB2.B2_QATU, 0) - ISNULL(SB2.B2_QEMP, 0) - ISNULL(SB2.B2_RESERVA, 0)
                    AS FLOAT
                ) ELSE 0 END
            ) AS work_in_process_available
        FROM SB2010 SB2 WITH (NOLOCK)
        WHERE SB2.D_E_L_E_T_ = ''
          AND RTRIM(SB2.B2_FILIAL) = {branch_param}
        GROUP BY SB2.B2_COD
    )
    """


def materials_base_cte(*, branch_param: str = "?") -> str:
    return f"""
    materials_base AS (
        SELECT
            RTRIM(SB1.B1_COD) AS product_code,
            RTRIM(SB1.B1_DESC) AS product_description,
            RTRIM(SB1.B1_TIPO) AS product_type,
            RTRIM(SB1.B1_UM) AS unit,
            RTRIM(SB1.B1_GRUPO) AS product_group,
            RTRIM(SB1.B1_MSBLQL) AS blocked_raw,
            CAST(ISNULL(SBZ.BZ_ESTSEG, 0) AS FLOAT) AS safety_stock,
            ISNULL(st.primary_stock, 0) AS primary_stock,
            ISNULL(st.work_in_process_stock, 0) AS work_in_process_stock,
            ISNULL(st.warehouse_50_stock, 0) AS warehouse_50_stock,
            ISNULL(st.warehouse_98_stock, 0) AS warehouse_98_stock,
            ISNULL(st.warehouse_99_stock, 0) AS warehouse_99_stock,
            (
                ISNULL(st.primary_stock, 0)
                + ISNULL(st.warehouse_98_stock, 0)
                + ISNULL(st.warehouse_99_stock, 0)
            ) AS available_stock,
            ISNULL(st.work_in_process_committed, 0) AS work_in_process_committed,
            ISNULL(st.work_in_process_available, 0) AS work_in_process_available,
            CASE
                WHEN ISNULL(SBZ.BZ_ESTSEG, 0) <= 0 THEN 'without_safety_stock'
                WHEN (
                    ISNULL(st.primary_stock, 0)
                    + ISNULL(st.warehouse_98_stock, 0)
                    + ISNULL(st.warehouse_99_stock, 0)
                ) < ISNULL(SBZ.BZ_ESTSEG, 0) - {TOLERANCE}
                    THEN 'below_safety_stock'
                WHEN ABS(
                    (
                        ISNULL(st.primary_stock, 0)
                        + ISNULL(st.warehouse_98_stock, 0)
                        + ISNULL(st.warehouse_99_stock, 0)
                    ) - ISNULL(SBZ.BZ_ESTSEG, 0)
                ) <= {TOLERANCE}
                    THEN 'at_safety_stock'
                ELSE 'above_safety_stock'
            END AS status,
            CASE
                WHEN ISNULL(SBZ.BZ_ESTSEG, 0) <= 0 THEN 0
                ELSE
                    CASE
                        WHEN ISNULL(SBZ.BZ_ESTSEG, 0) - (
                            ISNULL(st.primary_stock, 0)
                            + ISNULL(st.warehouse_98_stock, 0)
                            + ISNULL(st.warehouse_99_stock, 0)
                        ) > 0
                        THEN ISNULL(SBZ.BZ_ESTSEG, 0) - (
                            ISNULL(st.primary_stock, 0)
                            + ISNULL(st.warehouse_98_stock, 0)
                            + ISNULL(st.warehouse_99_stock, 0)
                        )
                        ELSE 0
                    END
            END AS deficit_quantity
        FROM SB1010 SB1 WITH (NOLOCK)
        LEFT JOIN SBZ010 SBZ WITH (NOLOCK)
            ON SBZ.BZ_COD = SB1.B1_COD
           AND SBZ.D_E_L_E_T_ = ''
           AND RTRIM(SBZ.BZ_FILIAL) = {branch_param}
           AND RTRIM(SBZ.BZ_FILIAL) <> ''
        LEFT JOIN stock_agg st
            ON st.product_code = RTRIM(SB1.B1_COD)
        WHERE SB1.D_E_L_E_T_ = ''
          AND SB1.B1_TIPO = 'MP'
    )
    """


def build_where_clauses(
    *,
    include_blocked: bool,
    product_group: str | None,
    unit: str | None,
    search: str | None,
    status: str | None,
    include_without_safety_stock: bool,
    table_alias: str = "materials_base",
) -> tuple[str, list]:
    clauses: list[str] = []
    params: list = []

    if not include_blocked:
        clauses.append(
            f"(RTRIM(LTRIM({table_alias}.blocked_raw)) NOT IN ('1', 'SIM') "
            f"OR {table_alias}.blocked_raw IS NULL "
            f"OR RTRIM(LTRIM({table_alias}.blocked_raw)) = '')"
        )

    if product_group:
        clauses.append(f"RTRIM({table_alias}.product_group) = ?")
        params.append(product_group.strip())

    if unit:
        clauses.append(f"RTRIM({table_alias}.unit) = ?")
        params.append(unit.strip())

    if search:
        term = search.strip()
        if term:
            clauses.append(
                f"(RTRIM({table_alias}.product_code) LIKE ? "
                f"OR RTRIM({table_alias}.product_description) COLLATE Latin1_General_CI_AI LIKE ?)"
            )
            params.extend([f"%{term}%", f"%{term}%"])

    if status:
        clauses.append(f"{table_alias}.status = ?")
        params.append(status.strip())

    if not include_without_safety_stock:
        clauses.append(f"{table_alias}.status <> 'without_safety_stock'")

    if not clauses:
        return "", params
    return " AND ".join(clauses), params


def resolve_order_by(sort_by: str, sort_direction: str) -> str:
    column = SORTABLE_COLUMNS.get(sort_by, "product_code")
    direction = "DESC" if str(sort_direction).lower() == "desc" else "ASC"
    if column == "product_code":
        return f"product_code {direction}"
    return f"{column} {direction}, product_code ASC"


def open_purchase_orders_sql(*, branch_param: str = "?", product_param: str = "?") -> str:
    """Pedidos de compra em aberto (SC7) por filial + produto."""
    return f"""
    SELECT
        RTRIM(SC7.C7_FILIAL) AS branch,
        RTRIM(SC7.C7_NUM) AS order_number,
        RTRIM(SC7.C7_ITEM) AS order_item,
        RTRIM(SC7.C7_PRODUTO) AS product_code,
        RTRIM(COALESCE(SB1.B1_DESC, SC7.C7_DESCRI)) AS product_description,
        RTRIM(SC7.C7_LOCAL) AS warehouse,
        RTRIM(SC7.C7_UM) AS unit,
        CAST(ISNULL(SC7.C7_QUANT, 0) AS FLOAT) AS ordered_quantity,
        CAST(ISNULL(SC7.C7_QUJE, 0) AS FLOAT) AS delivered_quantity,
        CAST(
            CASE
                WHEN SC7.C7_QUANT > SC7.C7_QUJE
                THEN SC7.C7_QUANT - SC7.C7_QUJE
                ELSE 0
            END AS FLOAT
        ) AS open_quantity,
        CAST(ISNULL(SC7.C7_QTDACLA, 0) AS FLOAT) AS pre_invoice_quantity,
        RTRIM(SC7.C7_EMISSAO) AS issue_date,
        RTRIM(SC7.C7_DATPRF) AS expected_delivery_date,
        RTRIM(SC7.C7_FORNECE) AS supplier_code,
        RTRIM(SC7.C7_LOJA) AS supplier_store,
        RTRIM(COALESCE(SA2.A2_NREDUZ, SA2.A2_NOME, '')) AS supplier_name,
        CAST(ISNULL(SC7.C7_PRECO, 0) AS FLOAT) AS unit_price,
        CAST(
            CASE
                WHEN SC7.C7_QUANT > SC7.C7_QUJE
                THEN (SC7.C7_QUANT - SC7.C7_QUJE) * ISNULL(SC7.C7_PRECO, 0)
                ELSE 0
            END AS FLOAT
        ) AS open_value
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
      AND RTRIM(SC7.C7_FILIAL) = {branch_param}
      AND RTRIM(SC7.C7_PRODUTO) = {product_param}
    ORDER BY
        CASE WHEN RTRIM(SC7.C7_DATPRF) = '' THEN 1 ELSE 0 END,
        SC7.C7_DATPRF ASC,
        SC7.C7_NUM ASC,
        SC7.C7_ITEM ASC
    """


def open_commitments_sql(*, branch_param: str = "?", product_param: str = "?") -> str:
    """Empenhos em aberto (SD4) por filial + produto — saldo atual em D4_QUANT.

    SD4010 não possui coluna de UM: D4_QUANT já está na unidade primária do
    produto (B1_UM); a segunda unidade fica em D4_QTSEGUM.
    """
    return f"""
    SELECT
        RTRIM(SD4.D4_FILIAL) AS branch,
        RTRIM(SD4.D4_COD) AS product_code,
        RTRIM(COALESCE(SB1.B1_DESC, '')) AS product_description,
        RTRIM(SD4.D4_LOCAL) AS warehouse,
        RTRIM(SD4.D4_OP) AS production_order,
        RTRIM(SD4.D4_OPORIG) AS origin_production_order,
        RTRIM(SD4.D4_DATA) AS commitment_date,
        RTRIM(COALESCE(SB1.B1_UM, '')) AS unit,
        CAST(ISNULL(SD4.D4_QTDEORI, 0) AS FLOAT) AS original_quantity,
        CAST(ISNULL(SD4.D4_QUANT, 0) AS FLOAT) AS open_quantity,
        CAST(
            CASE
                WHEN ISNULL(SD4.D4_QTDEORI, 0) > ISNULL(SD4.D4_QUANT, 0)
                THEN ISNULL(SD4.D4_QTDEORI, 0) - ISNULL(SD4.D4_QUANT, 0)
                ELSE 0
            END AS FLOAT
        ) AS consumed_quantity,
        RTRIM(SD4.D4_LOTECTL) AS lot,
        RTRIM(SD4.D4_TRT) AS commitment_sequence,
        CAST(ISNULL(SD4.D4_SLDEMP, 0) AS FLOAT) AS preserved_balance
    FROM SD4010 SD4 WITH (NOLOCK)
    LEFT JOIN SB1010 SB1 WITH (NOLOCK)
        ON SB1.B1_COD = SD4.D4_COD
       AND SB1.D_E_L_E_T_ = ''
    WHERE SD4.D_E_L_E_T_ = ''
      AND SD4.D4_QUANT > 0
      AND SD4.D4_FILIAL = {branch_param}
      AND SD4.D4_COD = {product_param}
    ORDER BY
        CASE WHEN RTRIM(SD4.D4_DATA) = '' THEN 1 ELSE 0 END,
        SD4.D4_DATA ASC,
        SD4.D4_OP ASC,
        SD4.D4_TRT ASC
    """


def product_detail_sql(*, branch_param: str = "?", product_param: str = "?") -> str:
    """Snapshot de uma MP com saldos e campos de conversão de unidade."""
    return f"""
    WITH
    {stock_agg_cte(branch_param=branch_param)}
    , {materials_base_cte(branch_param=branch_param)}
    SELECT
        mb.product_code,
        mb.product_description,
        mb.product_type,
        mb.unit,
        mb.product_group,
        mb.blocked_raw,
        mb.safety_stock,
        mb.primary_stock,
        mb.work_in_process_stock,
        mb.warehouse_50_stock,
        mb.warehouse_98_stock,
        mb.warehouse_99_stock,
        mb.available_stock,
        mb.work_in_process_committed,
        mb.work_in_process_available,
        mb.deficit_quantity,
        mb.status,
        RTRIM(SB1.B1_SEGUM) AS secondary_unit,
        CAST(ISNULL(SB1.B1_CONV, 0) AS FLOAT) AS conversion_factor,
        RTRIM(SB1.B1_TIPCONV) AS conversion_type
    FROM materials_base mb
    INNER JOIN SB1010 SB1 WITH (NOLOCK)
        ON RTRIM(SB1.B1_COD) = mb.product_code
       AND SB1.D_E_L_E_T_ = ''
    WHERE mb.product_code = {product_param}
    """


def linked_suppliers_sql(
    *,
    branch_param: str = "?",
    product_param: str = "?",
) -> str:
    """Fornecedores amarrados (SA5×SA2) com última compra do produto (SD1).

    Exclui fornecedores internos DELPI (transferência entre filiais) —
    ver ``safety_stock_supplier_scope_service``. Ordena por última compra
    (mais recente primeiro); fornecedores sem compra ficam por último.

    Params, na ordem de aparição dos placeholders:
    branch (SA5 rank), product (SA5), branch (SA5 filtro),
    product (SD1), branch (SD1).
    """
    return f"""
    WITH linked_sa5 AS (
        SELECT
            RTRIM(SA5.A5_PRODUTO) AS product_code,
            RTRIM(SA5.A5_FORNECE) AS supplier_code,
            RTRIM(SA5.A5_LOJA) AS supplier_store,
            RTRIM(ISNULL(SA5.A5_CODPRF, '')) AS supplier_part_number,
            ROW_NUMBER() OVER (
                PARTITION BY
                    RTRIM(SA5.A5_PRODUTO),
                    RTRIM(SA5.A5_FORNECE),
                    RTRIM(SA5.A5_LOJA)
                ORDER BY
                    CASE
                        WHEN RTRIM(SA5.A5_FILIAL) = {branch_param} THEN 0
                        WHEN RTRIM(ISNULL(SA5.A5_FILIAL, '')) = '' THEN 1
                        ELSE 2
                    END,
                    SA5.R_E_C_N_O_ DESC
            ) AS rn
        FROM SA5010 SA5 WITH (NOLOCK)
        WHERE SA5.D_E_L_E_T_ = ''
          AND RTRIM(SA5.A5_PRODUTO) = {product_param}
          AND RTRIM(SA5.A5_FORNECE) NOT IN ({internal_transfer_supplier_codes_sql()})
          AND (
              RTRIM(ISNULL(SA5.A5_FILIAL, '')) = ''
              OR RTRIM(SA5.A5_FILIAL) = {branch_param}
          )
    ),
    suppliers AS (
        SELECT
            product_code,
            supplier_code,
            supplier_store,
            supplier_part_number
        FROM linked_sa5
        WHERE rn = 1
    ),
    supplier_master AS (
        SELECT
            RTRIM(SA2.A2_COD) AS supplier_code,
            RTRIM(SA2.A2_LOJA) AS supplier_store,
            RTRIM(ISNULL(SA2.A2_NREDUZ, '')) AS trade_name,
            RTRIM(ISNULL(SA2.A2_NOME, '')) AS legal_name,
            RTRIM(ISNULL(SA2.A2_CGC, '')) AS document,
            ROW_NUMBER() OVER (
                PARTITION BY RTRIM(SA2.A2_COD), RTRIM(SA2.A2_LOJA)
                ORDER BY
                    CASE
                        WHEN RTRIM(ISNULL(SA2.A2_FILIAL, '')) = '' THEN 1
                        ELSE 0
                    END,
                    SA2.R_E_C_N_O_ DESC
            ) AS rn
        FROM SA2010 SA2 WITH (NOLOCK)
        INNER JOIN suppliers S
            ON S.supplier_code = RTRIM(SA2.A2_COD)
           AND S.supplier_store = RTRIM(SA2.A2_LOJA)
        WHERE SA2.D_E_L_E_T_ = ''
    ),
    last_purchase AS (
        SELECT
            RTRIM(SD1.D1_COD) AS product_code,
            RTRIM(SD1.D1_FORNECE) AS supplier_code,
            RTRIM(SD1.D1_LOJA) AS supplier_store,
            RTRIM(SD1.D1_DTDIGIT) AS last_purchase_date,
            CAST(ISNULL(SD1.D1_VUNIT, 0) AS FLOAT) AS last_unit_price,
            CAST(ISNULL(SD1.D1_QUANT, 0) AS FLOAT) AS last_quantity,
            CAST(ISNULL(SD1.D1_TOTAL, 0) AS FLOAT) AS last_total_value,
            RTRIM(ISNULL(SD1.D1_DOC, '')) AS last_invoice_number,
            RTRIM(ISNULL(SD1.D1_SERIE, '')) AS last_invoice_series,
            ROW_NUMBER() OVER (
                PARTITION BY
                    RTRIM(SD1.D1_COD),
                    RTRIM(SD1.D1_FORNECE),
                    RTRIM(SD1.D1_LOJA)
                ORDER BY
                    SD1.D1_DTDIGIT DESC,
                    SD1.D1_EMISSAO DESC,
                    SD1.R_E_C_N_O_ DESC
            ) AS rn
        FROM SD1010 SD1 WITH (NOLOCK)
        WHERE SD1.D_E_L_E_T_ = ''
          AND SD1.D1_TIPO = 'N'
          AND SD1.D1_QUANT > 0
          AND RTRIM(SD1.D1_COD) = {product_param}
          AND RTRIM(SD1.D1_FILIAL) = {branch_param}
    )
    SELECT
        S.product_code,
        S.supplier_code,
        S.supplier_store,
        S.supplier_part_number,
        RTRIM(ISNULL(SM.trade_name, '')) AS trade_name,
        RTRIM(ISNULL(SM.legal_name, '')) AS legal_name,
        RTRIM(ISNULL(SM.document, '')) AS document,
        LP.last_purchase_date,
        LP.last_unit_price,
        LP.last_quantity,
        LP.last_total_value,
        LP.last_invoice_number,
        LP.last_invoice_series,
        CASE WHEN LP.product_code IS NULL THEN 0 ELSE 1 END AS has_last_purchase
    FROM suppliers S
    LEFT JOIN supplier_master SM
        ON SM.supplier_code = S.supplier_code
       AND SM.supplier_store = S.supplier_store
       AND SM.rn = 1
    LEFT JOIN last_purchase LP
        ON LP.product_code = S.product_code
       AND LP.supplier_code = S.supplier_code
       AND LP.supplier_store = S.supplier_store
       AND LP.rn = 1
    ORDER BY
        CASE WHEN LP.product_code IS NULL THEN 1 ELSE 0 END,
        LP.last_purchase_date DESC,
        CASE
            WHEN RTRIM(ISNULL(SM.trade_name, '')) <> '' THEN SM.trade_name
            WHEN RTRIM(ISNULL(SM.legal_name, '')) <> '' THEN SM.legal_name
            ELSE S.supplier_code
        END ASC,
        S.supplier_code ASC,
        S.supplier_store ASC
    """
