"""SQL builders — análise de estoque de segurança (MP × SBZ × SB2)."""

from __future__ import annotations

from app.domain.services.supplies.safety_stock_classification_service import (
    AVAILABLE_BALANCE_WAREHOUSES,
    PRIMARY_WAREHOUSE,
    TOLERANCE,
    WORK_IN_PROCESS_WAREHOUSES,
)
from app.domain.services.supplies.safety_stock_consumption_analysis_service import (
    CONSUMPTION_MOVEMENT_TYPE,
    CONSUMPTION_WAREHOUSE,
)
from app.domain.services.supplies.safety_stock_supplier_scope_service import (
    INTERNAL_TRANSFER_SUPPLIER_CODES,
    internal_transfer_supplier_codes_sql,
)
from app.domain.totvs.protheus_branches import branch_filter_sql
from app.domain.totvs.protheus_product_types import (
    PRODUCT_TYPE_LABELS_PT,
    PRODUCT_TYPE_RAW_MATERIAL,
)


def branch_filter_and(column: str, scope: str) -> tuple[str, list]:
    """Todas → sem predicado; 01/02 → ``AND column = ?``."""
    clause, params = branch_filter_sql(column, scope)
    if not clause:
        return "", []
    return f"AND {clause}", list(params)

__all__ = [
    "AVAILABLE_BALANCE_WAREHOUSES",
    "INTERNAL_TRANSFER_SUPPLIER_CODES",
    "PRIMARY_WAREHOUSE",
    "TOLERANCE",
    "WORK_IN_PROCESS_WAREHOUSES",
    "SORTABLE_COLUMNS",
    "build_consumption_analysis_where_clauses",
    "build_where_clauses",
    "consumption_agg_cte",
    "consumption_analysis_rows_sql",
    "consumption_last_date_sql",
    "consumption_monthly_series_sql",
    "last_inventory_date_sql",
    "last_inventory_dates_batch_sql",
    "linked_suppliers_sql",
    "materials_base_cte",
    "available_stock_for_open_purchase_request_products_sql",
    "open_commitments_sql",
    "open_purchase_orders_sql",
    "open_purchase_requests_sql",
    "compute_open_purchase_order_item_value",
    "compute_open_purchase_order_item_components",
    "materials_for_projection_batch_sql",
    "last_inbound_party_names_sql",
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


def stock_agg_cte(*, branch: str) -> tuple[str, list]:
    wip = _wip_locals_sql()
    and_sql, params = branch_filter_and("RTRIM(SB2.B2_FILIAL)", branch)
    sql = f"""
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
          {and_sql}
        GROUP BY SB2.B2_COD
    )
    """
    return sql, params


def materials_base_cte(*, branch: str) -> tuple[str, list]:
    and_sql, params = branch_filter_and("RTRIM(S.BZ_FILIAL)", branch)
    sql = f"""
    materials_base AS (
        SELECT
            RTRIM(SB1.B1_COD) AS product_code,
            RTRIM(SB1.B1_DESC) AS product_description,
            RTRIM(SB1.B1_TIPO) AS product_type,
            RTRIM(SB1.B1_UM) AS unit,
            RTRIM(SB1.B1_GRUPO) AS product_group,
            RTRIM(SB1.B1_MSBLQL) AS blocked_raw,
            CAST(ISNULL(SBZ.BZ_ESTSEG, 0) AS FLOAT) AS safety_stock,
            CAST(ISNULL(SBZ.BZ_PE, 0) AS FLOAT) AS lead_time_days,
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
        OUTER APPLY (
            SELECT
                SUM(CAST(ISNULL(S.BZ_ESTSEG, 0) AS FLOAT)) AS BZ_ESTSEG,
                MAX(CAST(ISNULL(S.BZ_PE, 0) AS FLOAT)) AS BZ_PE
            FROM SBZ010 S WITH (NOLOCK)
            WHERE S.BZ_COD = SB1.B1_COD
              AND S.D_E_L_E_T_ = ''
              AND RTRIM(S.BZ_FILIAL) <> ''
              {and_sql}
        ) SBZ
        LEFT JOIN stock_agg st
            ON st.product_code = RTRIM(SB1.B1_COD)
        WHERE SB1.D_E_L_E_T_ = ''
          AND SB1.B1_TIPO = 'MP'
    )
    """
    return sql, params


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


def compute_open_purchase_order_item_components(
    *,
    quantity: float,
    delivered_quantity: float,
    merchandise_total: float,
    ipi_value: float,
    freight_value: float,
    discount_value: float,
) -> dict[str, float]:
    """Componentes proporcionais do open_value em open_purchase_orders_sql (SC7).

    Fator = (C7_QUANT - C7_QUJE) / C7_QUANT
    Cada componente arredondado em 2 casas antes da soma.
    Não inclui C7_VALICM / C7_ICMCOMP / C7_FRETE.
    """
    qty = float(quantity or 0)
    delivered = float(delivered_quantity or 0)
    if qty <= 0 or qty <= delivered:
        return {
            "open_merchandise_value": 0.0,
            "open_ipi_value": 0.0,
            "open_freight_value": 0.0,
            "open_discount_value": 0.0,
            "open_value": 0.0,
        }
    factor = (qty - delivered) / qty

    def _component(raw: float) -> float:
        return round(float(raw or 0) * factor, 2)

    merchandise = _component(merchandise_total)
    ipi = _component(ipi_value)
    freight = _component(freight_value)
    discount = _component(discount_value)
    return {
        "open_merchandise_value": merchandise,
        "open_ipi_value": ipi,
        "open_freight_value": freight,
        "open_discount_value": discount,
        "open_value": round(merchandise + ipi + freight - discount, 2),
    }


def compute_open_purchase_order_item_value(
    *,
    quantity: float,
    delivered_quantity: float,
    merchandise_total: float,
    ipi_value: float,
    freight_value: float,
    discount_value: float,
) -> float:
    """Espelho Python do open_value em open_purchase_orders_sql (SC7)."""
    return compute_open_purchase_order_item_components(
        quantity=quantity,
        delivered_quantity=delivered_quantity,
        merchandise_total=merchandise_total,
        ipi_value=ipi_value,
        freight_value=freight_value,
        discount_value=discount_value,
    )["open_value"]


def open_purchase_orders_sql(
    *,
    branch: str,
    product_param: str | None = "?",
    supplier_code_param: str | None = None,
    supplier_store_param: str | None = None,
) -> tuple[str, list]:
    """Pedidos de compra em aberto (SC7) por filial (+ produto e/ou fornecedor opcionais).

    Componentes proporcionais ao saldo:
    fator = (C7_QUANT - C7_QUJE) / C7_QUANT;
    open_merchandise_value = ROUND(C7_TOTAL*f,2);
    open_ipi_value = ROUND(C7_VALIPI*f,2);
    open_value = mercadoria + IPI + frete - desconto.
    """
    product_clause = ""
    if product_param is not None:
        product_clause = f"AND RTRIM(SC7.C7_PRODUTO) = {product_param}"
    supplier_clause = ""
    if supplier_code_param is not None:
        supplier_clause += f"\n      AND RTRIM(SC7.C7_FORNECE) = {supplier_code_param}"
    if supplier_store_param is not None:
        supplier_clause += f"\n      AND RTRIM(SC7.C7_LOJA) = {supplier_store_param}"
    and_sql, params = branch_filter_and("RTRIM(SC7.C7_FILIAL)", branch)
    sql = f"""
    SELECT
        RTRIM(SC7.C7_FILIAL) AS branch,
        RTRIM(SC7.C7_NUM) AS order_number,
        RTRIM(SC7.C7_ITEM) AS order_item,
        RTRIM(SC7.C7_PRODUTO) AS product_code,
        RTRIM(COALESCE(SB1.B1_DESC, SC7.C7_DESCRI)) AS product_description,
        RTRIM(ISNULL(SA5pn.supplier_part_number, '')) AS supplier_part_number,
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
            ROUND(ISNULL(SC7.C7_TOTAL, 0) * bf.balance_factor, 2) AS FLOAT
        ) AS open_merchandise_value,
        CAST(
            ROUND(ISNULL(SC7.C7_VALIPI, 0) * bf.balance_factor, 2) AS FLOAT
        ) AS open_ipi_value,
        CAST(
            ROUND(ISNULL(SC7.C7_VALFRE, 0) * bf.balance_factor, 2) AS FLOAT
        ) AS open_freight_value,
        CAST(
            ROUND(ISNULL(SC7.C7_VLDESC, 0) * bf.balance_factor, 2) AS FLOAT
        ) AS open_discount_value,
        CAST(
            ROUND(ISNULL(SC7.C7_TOTAL, 0) * bf.balance_factor, 2)
            + ROUND(ISNULL(SC7.C7_VALIPI, 0) * bf.balance_factor, 2)
            + ROUND(ISNULL(SC7.C7_VALFRE, 0) * bf.balance_factor, 2)
            - ROUND(ISNULL(SC7.C7_VLDESC, 0) * bf.balance_factor, 2)
            AS FLOAT
        ) AS open_value
    FROM SC7010 SC7 WITH (NOLOCK)
    CROSS APPLY (
        SELECT
            CASE
                WHEN ISNULL(SC7.C7_QUANT, 0) <= 0 THEN CAST(0 AS FLOAT)
                WHEN SC7.C7_QUANT > SC7.C7_QUJE
                THEN (SC7.C7_QUANT - SC7.C7_QUJE) * 1.0 / SC7.C7_QUANT
                ELSE CAST(0 AS FLOAT)
            END AS balance_factor
    ) bf
    LEFT JOIN SB1010 SB1 WITH (NOLOCK)
        ON SB1.B1_COD = SC7.C7_PRODUTO
       AND SB1.D_E_L_E_T_ = ''
    LEFT JOIN SA2010 SA2 WITH (NOLOCK)
        ON SA2.A2_COD = SC7.C7_FORNECE
       AND SA2.A2_LOJA = SC7.C7_LOJA
       AND SA2.D_E_L_E_T_ = ''
    OUTER APPLY (
        SELECT TOP 1
            RTRIM(ISNULL(SA5.A5_CODPRF, '')) AS supplier_part_number
        FROM SA5010 SA5 WITH (NOLOCK)
        WHERE SA5.D_E_L_E_T_ = ''
          AND RTRIM(SA5.A5_PRODUTO) = RTRIM(SC7.C7_PRODUTO)
          AND RTRIM(SA5.A5_FORNECE) = RTRIM(SC7.C7_FORNECE)
          AND RTRIM(SA5.A5_LOJA) = RTRIM(SC7.C7_LOJA)
          AND (
              RTRIM(ISNULL(SA5.A5_FILIAL, '')) = ''
              OR RTRIM(SA5.A5_FILIAL) = RTRIM(SC7.C7_FILIAL)
          )
        ORDER BY
            CASE
                WHEN RTRIM(SA5.A5_FILIAL) = RTRIM(SC7.C7_FILIAL) THEN 0
                WHEN RTRIM(ISNULL(SA5.A5_FILIAL, '')) = '' THEN 1
                ELSE 2
            END,
            SA5.R_E_C_N_O_ DESC
    ) SA5pn
    WHERE SC7.D_E_L_E_T_ = ''
      AND ISNULL(SC7.C7_RESIDUO, '') <> 'S'
      AND SC7.C7_QUANT > SC7.C7_QUJE
      {and_sql}
      {product_clause}
      {supplier_clause}
    ORDER BY
        CASE WHEN RTRIM(SC7.C7_DATPRF) = '' THEN 1 ELSE 0 END,
        SC7.C7_DATPRF ASC,
        SC7.C7_NUM ASC,
        SC7.C7_ITEM ASC
    """
    return sql, params


def open_purchase_requests_sql(
    *,
    branch: str,
    product_param: str | None = "?",
    product_type: str | None = None,
) -> tuple[str, list]:
    """Solicitações de compra em aberto (SC1) por filial (+ produto opcional).

    Saldo aberto: ``C1_QUANT > C1_QUJE`` e residual diferente de ``S``.
    Informativo no detalhe — **não** entra na projeção (evita doble-conta com SC7).
    ``product_type`` restringe ``SB1.B1_TIPO`` (dump PCP: só MP).
    """
    product_clause = ""
    if product_param is not None:
        product_clause = f"AND RTRIM(SC1.C1_PRODUTO) = {product_param}"
    type_clause = ""
    if product_type:
        normalized_type = product_type.strip().upper()
        if normalized_type not in PRODUCT_TYPE_LABELS_PT:
            raise ValueError(f"unsupported product_type: {product_type}")
        type_clause = f"AND RTRIM(SB1.B1_TIPO) = '{normalized_type}'"
    and_sql, params = branch_filter_and("RTRIM(SC1.C1_FILIAL)", branch)
    sql = f"""
    SELECT
        RTRIM(SC1.C1_FILIAL) AS branch,
        RTRIM(SC1.C1_NUM) AS request_number,
        RTRIM(SC1.C1_ITEM) AS request_item,
        RTRIM(SC1.C1_PRODUTO) AS product_code,
        RTRIM(COALESCE(SB1.B1_DESC, SC1.C1_DESCRI, '')) AS product_description,
        RTRIM(ISNULL(SC1.C1_LOCAL, '')) AS warehouse,
        RTRIM(ISNULL(SC1.C1_UM, '')) AS unit,
        CAST(ISNULL(SC1.C1_QUANT, 0) AS FLOAT) AS requested_quantity,
        CAST(ISNULL(SC1.C1_QUJE, 0) AS FLOAT) AS ordered_quantity,
        CAST(
            CASE
                WHEN SC1.C1_QUANT > SC1.C1_QUJE
                THEN SC1.C1_QUANT - SC1.C1_QUJE
                ELSE 0
            END AS FLOAT
        ) AS open_quantity,
        RTRIM(SC1.C1_EMISSAO) AS issue_date,
        RTRIM(SC1.C1_DATPRF) AS required_date,
        RTRIM(ISNULL(SC1.C1_FORNECE, '')) AS supplier_code,
        RTRIM(ISNULL(SC1.C1_LOJA, '')) AS supplier_store,
        RTRIM(COALESCE(SA2.A2_NREDUZ, SA2.A2_NOME, '')) AS supplier_name,
        RTRIM(ISNULL(SC1.C1_PEDIDO, '')) AS purchase_order_number,
        CAST(ISNULL(SC1.C1_PRECO, 0) AS FLOAT) AS unit_price,
        CAST(ISNULL(SC1.C1_TOTAL, 0) AS FLOAT) AS total_value
    FROM SC1010 SC1 WITH (NOLOCK)
    LEFT JOIN SB1010 SB1 WITH (NOLOCK)
        ON SB1.B1_COD = SC1.C1_PRODUTO
       AND SB1.D_E_L_E_T_ = ''
    LEFT JOIN SA2010 SA2 WITH (NOLOCK)
        ON SA2.A2_COD = SC1.C1_FORNECE
       AND SA2.A2_LOJA = SC1.C1_LOJA
       AND SA2.D_E_L_E_T_ = ''
    WHERE SC1.D_E_L_E_T_ = ''
      AND ISNULL(SC1.C1_RESIDUO, '') <> 'S'
      AND SC1.C1_QUANT > SC1.C1_QUJE
      {and_sql}
      {product_clause}
      {type_clause}
    ORDER BY
        CASE WHEN RTRIM(SC1.C1_DATPRF) = '' THEN 1 ELSE 0 END,
        SC1.C1_DATPRF ASC,
        SC1.C1_NUM ASC,
        SC1.C1_ITEM ASC
    """
    return sql, params


def available_stock_for_open_purchase_request_products_sql(
    *,
    branch: str,
) -> tuple[str, list]:
    """Saldo 01+98+99, ESTSEG (SBZ) e UM das MPs com SC1 aberta ou estoque de segurança."""
    request_and_sql, request_params = branch_filter_and("RTRIM(SC1.C1_FILIAL)", branch)
    estseg_and_sql, estseg_params = branch_filter_and("RTRIM(SZ.BZ_FILIAL)", branch)
    stock_and_sql, stock_params = branch_filter_and("RTRIM(SB2.B2_FILIAL)", branch)
    sbz_and_sql, sbz_params = branch_filter_and("RTRIM(S.BZ_FILIAL)", branch)
    locals_sql = ", ".join(f"'{code}'" for code in AVAILABLE_BALANCE_WAREHOUSES)
    sql = f"""
    WITH open_sc1 AS (
        SELECT DISTINCT RTRIM(SC1.C1_PRODUTO) AS product_code
        FROM SC1010 SC1 WITH (NOLOCK)
        INNER JOIN SB1010 SB1 WITH (NOLOCK)
            ON SB1.B1_COD = SC1.C1_PRODUTO
           AND SB1.D_E_L_E_T_ = ''
           AND RTRIM(SB1.B1_TIPO) = '{PRODUCT_TYPE_RAW_MATERIAL}'
        WHERE SC1.D_E_L_E_T_ = ''
          AND ISNULL(SC1.C1_RESIDUO, '') <> 'S'
          AND SC1.C1_QUANT > SC1.C1_QUJE
          {request_and_sql}
    ),
    safety_targets AS (
        SELECT RTRIM(SB1.B1_COD) AS product_code
        FROM SB1010 SB1 WITH (NOLOCK)
        WHERE SB1.D_E_L_E_T_ = ''
          AND RTRIM(SB1.B1_TIPO) = '{PRODUCT_TYPE_RAW_MATERIAL}'
          AND EXISTS (
              SELECT 1
              FROM SBZ010 SZ WITH (NOLOCK)
              WHERE SZ.BZ_COD = SB1.B1_COD
                AND SZ.D_E_L_E_T_ = ''
                AND RTRIM(SZ.BZ_FILIAL) <> ''
                AND CAST(ISNULL(SZ.BZ_ESTSEG, 0) AS FLOAT) > 0
                {estseg_and_sql}
          )
    ),
    coverage_products AS (
        SELECT product_code FROM open_sc1
        UNION
        SELECT product_code FROM safety_targets
    ),
    stock_agg AS (
        SELECT
            RTRIM(SB2.B2_COD) AS product_code,
            SUM(
                CASE WHEN RTRIM(SB2.B2_LOCAL) IN ({locals_sql})
                THEN CAST(ISNULL(SB2.B2_QATU, 0) AS FLOAT) ELSE 0 END
            ) AS available_stock
        FROM SB2010 SB2 WITH (NOLOCK)
        INNER JOIN coverage_products p
            ON p.product_code = RTRIM(SB2.B2_COD)
        WHERE SB2.D_E_L_E_T_ = ''
          {stock_and_sql}
        GROUP BY SB2.B2_COD
    ),
    sbz_agg AS (
        SELECT
            RTRIM(S.BZ_COD) AS product_code,
            SUM(CAST(ISNULL(S.BZ_ESTSEG, 0) AS FLOAT)) AS safety_stock
        FROM SBZ010 S WITH (NOLOCK)
        INNER JOIN coverage_products p
            ON p.product_code = RTRIM(S.BZ_COD)
        WHERE S.D_E_L_E_T_ = ''
          AND RTRIM(S.BZ_FILIAL) <> ''
          {sbz_and_sql}
        GROUP BY S.BZ_COD
    )
    SELECT
        p.product_code,
        RTRIM(COALESCE(SB1.B1_DESC, '')) AS product_description,
        RTRIM(ISNULL(SB1.B1_UM, '')) AS unit,
        RTRIM(ISNULL(SB1.B1_SEGUM, '')) AS secondary_unit,
        CAST(ISNULL(SB1.B1_CONV, 0) AS FLOAT) AS conversion_factor,
        RTRIM(ISNULL(SB1.B1_TIPCONV, '')) AS conversion_type,
        ISNULL(st.available_stock, 0) AS available_stock,
        ISNULL(sz.safety_stock, 0) AS safety_stock
    FROM coverage_products p
    LEFT JOIN SB1010 SB1 WITH (NOLOCK)
        ON SB1.B1_COD = p.product_code
       AND SB1.D_E_L_E_T_ = ''
    LEFT JOIN stock_agg st
        ON st.product_code = p.product_code
    LEFT JOIN sbz_agg sz
        ON sz.product_code = p.product_code
    ORDER BY p.product_code ASC
    """
    return sql, request_params + estseg_params + stock_params + sbz_params


def open_commitments_sql(
    *,
    branch: str,
    product_param: str | None = "?",
) -> tuple[str, list]:
    """Empenhos em aberto (SD4) por filial (+ produto opcional) — saldo em D4_QUANT.

    SD4010 não possui coluna de UM: D4_QUANT já está na unidade primária do
    produto (B1_UM); a segunda unidade fica em D4_QTSEGUM.

    Data de projeção: ``C2_DATPRI`` da OP do próprio empenho (``D4_OP`` → SC2),
    não ``D4_DATA`` nem a data da OP do produto acabado.

    Produto acabado: OP do empenho com os 6 primeiros dígitos + sufixo 01001
    (ex.: 24608101003 → 24608101001), resolvido em SC2.C2_PRODUTO.
    """
    product_clause = ""
    if product_param is not None:
        product_clause = f"AND SD4.D4_COD = {product_param}"
    and_sql, params = branch_filter_and("SD4.D4_FILIAL", branch)
    sql = f"""
    SELECT
        RTRIM(SD4.D4_FILIAL) AS branch,
        RTRIM(SD4.D4_COD) AS product_code,
        RTRIM(COALESCE(SB1.B1_DESC, '')) AS product_description,
        RTRIM(SD4.D4_LOCAL) AS warehouse,
        RTRIM(SD4.D4_OP) AS production_order,
        RTRIM(SD4.D4_OPORIG) AS origin_production_order,
        RTRIM(COALESCE(EMP.C2_DATPRI, '')) AS commitment_date,
        RTRIM(SD4.D4_DATA) AS empenho_recorded_date,
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
        CAST(ISNULL(SD4.D4_SLDEMP, 0) AS FLOAT) AS preserved_balance,
        CASE
            WHEN LEN(RTRIM(SD4.D4_OP)) >= 6
            THEN LEFT(RTRIM(SD4.D4_OP), 6) + '01001'
            ELSE NULL
        END AS finished_production_order,
        RTRIM(COALESCE(FP.C2_PRODUTO, '')) AS finished_product_code,
        RTRIM(COALESCE(FP.C2_OBS, '')) AS finished_order_observation
    FROM SD4010 SD4 WITH (NOLOCK)
    LEFT JOIN SB1010 SB1 WITH (NOLOCK)
        ON SB1.B1_COD = SD4.D4_COD
       AND SB1.D_E_L_E_T_ = ''
    LEFT JOIN SC2010 EMP WITH (NOLOCK)
        ON EMP.D_E_L_E_T_ = ''
       AND EMP.C2_FILIAL = SD4.D4_FILIAL
       AND RTRIM(LTRIM(EMP.C2_OP)) = RTRIM(LTRIM(SD4.D4_OP))
    LEFT JOIN SC2010 FP WITH (NOLOCK)
        ON FP.D_E_L_E_T_ = ''
       AND FP.C2_FILIAL = SD4.D4_FILIAL
       AND LEN(RTRIM(SD4.D4_OP)) >= 6
       AND RTRIM(LTRIM(FP.C2_OP)) = LEFT(RTRIM(SD4.D4_OP), 6) + '01001'
    WHERE SD4.D_E_L_E_T_ = ''
      AND SD4.D4_QUANT > 0
      {and_sql}
      {product_clause}
    ORDER BY
        CASE WHEN RTRIM(COALESCE(EMP.C2_DATPRI, '')) = '' THEN 1 ELSE 0 END,
        EMP.C2_DATPRI ASC,
        SD4.D4_OP ASC,
        SD4.D4_TRT ASC
    """
    return sql, params


def materials_for_projection_batch_sql(*, branch: str, where_sql: str = "") -> tuple[str, list]:
    """Todas as MPs da filial com saldo + conversão UM (sem paginação)."""
    where_prefix = f"WHERE {where_sql}" if where_sql else ""
    stock_sql, stock_params = stock_agg_cte(branch=branch)
    mat_sql, mat_params = materials_base_cte(branch=branch)
    sql = f"""
    WITH
    {stock_sql}
    , {mat_sql}
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
        RTRIM(SB1.B1_TIPCONV) AS conversion_type,
        RTRIM(SB1.B1_TPMAT) AS material_type
    FROM materials_base mb
    INNER JOIN SB1010 SB1 WITH (NOLOCK)
        ON RTRIM(SB1.B1_COD) = mb.product_code
       AND SB1.D_E_L_E_T_ = ''
    {where_prefix}
    ORDER BY mb.product_code ASC
    """
    return sql, stock_params + mat_params


def last_inbound_party_names_sql(*, branch: str, placeholders: str) -> tuple[str, list]:
    """Última NF de entrada (beneficiamento) por produto → cliente (SA1)."""
    and_sql, params = branch_filter_and("SD1.D1_FILIAL", branch)
    sql = f"""
    WITH ultima AS (
        SELECT
            RTRIM(SD1.D1_COD) AS product_code,
            RTRIM(
                COALESCE(
                    NULLIF(RTRIM(SA1.A1_NREDUZ), ''),
                    NULLIF(RTRIM(SA1.A1_NOME), ''),
                    RTRIM(SD1.D1_FORNECE)
                )
            ) AS party_name,
            ROW_NUMBER() OVER (
                PARTITION BY SD1.D1_COD
                ORDER BY
                    SD1.D1_EMISSAO DESC,
                    SD1.D1_DTDIGIT DESC,
                    SD1.D1_DOC DESC
            ) AS rn
        FROM SD1010 SD1 WITH (NOLOCK)
        LEFT JOIN SA1010 SA1 WITH (NOLOCK)
            ON SA1.A1_COD = SD1.D1_FORNECE
           AND SA1.A1_LOJA = SD1.D1_LOJA
           AND SA1.D_E_L_E_T_ = ''
        WHERE SD1.D_E_L_E_T_ = ''
          AND SD1.D1_TIPO = 'B'
          AND SD1.D1_QUANT > 0
          {and_sql}
          AND SD1.D1_COD IN ({placeholders})
    )
    SELECT product_code, party_name
    FROM ultima
    WHERE rn = 1
    """
    return sql, params


def product_detail_sql(*, branch: str, product_param: str = "?") -> tuple[str, list]:
    """Snapshot de uma MP com saldos e campos de conversão de unidade."""
    stock_sql, stock_params = stock_agg_cte(branch=branch)
    mat_sql, mat_params = materials_base_cte(branch=branch)
    sql = f"""
    WITH
    {stock_sql}
    , {mat_sql}
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
    return sql, stock_params + mat_params


def linked_suppliers_sql(
    *,
    branch: str,
    product_param: str = "?",
) -> tuple[str, list]:
    """Fornecedores amarrados (SA5×SA2) com última compra do produto (SD1)."""
    sa5_clause, sa5_params = branch_filter_and("RTRIM(SA5.A5_FILIAL)", branch)
    if sa5_params:
        rank_case = """
                    CASE
                        WHEN RTRIM(SA5.A5_FILIAL) = ? THEN 0
                        WHEN RTRIM(ISNULL(SA5.A5_FILIAL, '')) = '' THEN 1
                        ELSE 2
                    END"""
        rank_params = list(sa5_params)
        sa5_filter = """
          AND (
              RTRIM(ISNULL(SA5.A5_FILIAL, '')) = ''
              OR RTRIM(SA5.A5_FILIAL) = ?
          )"""
        sa5_filter_params = list(sa5_params)
    else:
        rank_case = """
                    CASE
                        WHEN RTRIM(ISNULL(SA5.A5_FILIAL, '')) = '' THEN 1
                        ELSE 0
                    END"""
        rank_params = []
        sa5_filter = ""
        sa5_filter_params = []

    sd1_and, sd1_params = branch_filter_and("RTRIM(SD1.D1_FILIAL)", branch)
    params = rank_params + sa5_filter_params + sd1_params
    sql = f"""
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
                    {rank_case},
                    SA5.R_E_C_N_O_ DESC
            ) AS rn
        FROM SA5010 SA5 WITH (NOLOCK)
        WHERE SA5.D_E_L_E_T_ = ''
          AND RTRIM(SA5.A5_PRODUTO) = {product_param}
          AND RTRIM(SA5.A5_FORNECE) NOT IN ({internal_transfer_supplier_codes_sql()})
          {sa5_filter}
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
          {sd1_and}
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
    return sql, params


def consumption_agg_cte(
    *,
    branch: str,
    start_date_param: str = "?",
) -> tuple[str, list]:
    """Agrega baixas SD3 elegíveis (local 99, TM 999, OP preenchida)."""
    and_sql, params = branch_filter_and("RTRIM(SD3.D3_FILIAL)", branch)
    sql = f"""
    consumption_agg AS (
        SELECT
            RTRIM(SD3.D3_COD) AS product_code,
            SUM(CAST(ISNULL(SD3.D3_QUANT, 0) AS FLOAT)) AS period_consumption,
            COUNT(*) AS movement_count,
            MIN(RTRIM(SD3.D3_EMISSAO)) AS first_movement_date,
            MAX(RTRIM(SD3.D3_EMISSAO)) AS last_movement_date
        FROM SD3010 SD3 WITH (NOLOCK)
        WHERE SD3.D_E_L_E_T_ = ''
          {and_sql}
          AND RTRIM(SD3.D3_LOCAL) = '{CONSUMPTION_WAREHOUSE}'
          AND LTRIM(RTRIM(ISNULL(SD3.D3_OP, ''))) <> ''
          AND RTRIM(SD3.D3_TM) = '{CONSUMPTION_MOVEMENT_TYPE}'
          AND SD3.D3_EMISSAO >= {start_date_param}
        GROUP BY SD3.D3_COD
        HAVING COUNT(*) > 0
    )
    """
    return sql, params


def build_consumption_analysis_where_clauses(
    *,
    include_blocked: bool,
    product_group: str | None,
    unit: str | None,
    search: str | None,
    product_code: str | None = None,
    table_alias: str = "analyzed",
) -> tuple[str, list]:
    clauses: list[str] = [f"{table_alias}.safety_stock <> 0"]
    params: list = []

    if not include_blocked:
        clauses.append(
            f"(RTRIM(LTRIM({table_alias}.blocked_raw)) NOT IN ('1', 'SIM') "
            f"OR {table_alias}.blocked_raw IS NULL "
            f"OR RTRIM(LTRIM({table_alias}.blocked_raw)) = '')"
        )

    if product_code:
        clauses.append(f"RTRIM({table_alias}.product_code) = ?")
        params.append(product_code.strip())

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
                f"OR RTRIM({table_alias}.product_description) "
                f"COLLATE Latin1_General_CI_AI LIKE ?)"
            )
            params.extend([f"%{term}%", f"%{term}%"])

    return " AND ".join(clauses), params


def consumption_analysis_rows_sql(
    *,
    branch: str,
    start_date_param: str = "?",
) -> tuple[str, list]:
    """Produtos com ESTSEG ≠ 0 e pelo menos uma baixa elegível no período."""
    stock_sql, stock_params = stock_agg_cte(branch=branch)
    mat_sql, mat_params = materials_base_cte(branch=branch)
    cons_sql, cons_params = consumption_agg_cte(
        branch=branch, start_date_param=start_date_param
    )
    sql = f"""
    WITH
    {stock_sql}
    , {mat_sql}
    , {cons_sql}
    , analyzed AS (
        SELECT
            mb.product_code,
            mb.product_description,
            mb.product_type,
            mb.unit,
            mb.product_group,
            mb.blocked_raw,
            mb.safety_stock,
            mb.lead_time_days,
            mb.primary_stock,
            mb.work_in_process_stock,
            mb.warehouse_50_stock,
            mb.warehouse_98_stock,
            mb.warehouse_99_stock,
            mb.available_stock,
            mb.work_in_process_committed,
            mb.work_in_process_available,
            ca.period_consumption,
            ca.movement_count,
            ca.first_movement_date,
            ca.last_movement_date
        FROM materials_base mb
        INNER JOIN consumption_agg ca
            ON ca.product_code = mb.product_code
    )
    SELECT *
    FROM analyzed
    WHERE {{where_sql}}
    ORDER BY product_code ASC
    """
    return sql, stock_params + mat_params + cons_params


def consumption_last_date_sql(
    *,
    branch: str,
    product_param: str = "?",
) -> tuple[str, list]:
    """Última baixa elegível (consumo SD3) de um produto na filial — sem janela de datas."""
    and_sql, params = branch_filter_and("RTRIM(SD3.D3_FILIAL)", branch)
    sql = f"""
    SELECT TOP 1
        RTRIM(SD3.D3_EMISSAO) AS last_consumption_date
    FROM SD3010 SD3 WITH (NOLOCK)
    WHERE SD3.D_E_L_E_T_ = ''
      {and_sql}
      AND RTRIM(SD3.D3_COD) = {product_param}
      AND RTRIM(SD3.D3_LOCAL) = '{CONSUMPTION_WAREHOUSE}'
      AND LTRIM(RTRIM(ISNULL(SD3.D3_OP, ''))) <> ''
      AND RTRIM(SD3.D3_TM) = '{CONSUMPTION_MOVEMENT_TYPE}'
    ORDER BY SD3.D3_EMISSAO DESC, SD3.R_E_C_N_O_ DESC
    """
    return sql, params


def last_inventory_date_sql(
    *,
    branch: str,
    product_param: str = "?",
) -> tuple[str, list]:
    """Última data de inventário (SB7.B7_DATA) do produto na filial."""
    and_sql, params = branch_filter_and("RTRIM(SB7.B7_FILIAL)", branch)
    sql = f"""
    SELECT
        MAX(RTRIM(SB7.B7_DATA)) AS last_inventory_date
    FROM SB7010 SB7 WITH (NOLOCK)
    WHERE SB7.D_E_L_E_T_ = ''
      {and_sql}
      AND RTRIM(SB7.B7_COD) = {product_param}
      AND NULLIF(RTRIM(SB7.B7_DATA), '') IS NOT NULL
    """
    return sql, params


def last_inventory_dates_batch_sql(*, placeholders: str) -> str:
    """Última data de inventário (SB7) por produto — batch.

    Placeholders: ``B7_FILIAL``, depois ``B7_COD IN (...)``.
    """
    return f"""
    SELECT
        RTRIM(SB7.B7_COD) AS product_code,
        MAX(RTRIM(SB7.B7_DATA)) AS last_inventory_date
    FROM SB7010 SB7 WITH (NOLOCK)
    WHERE SB7.D_E_L_E_T_ = ''
      AND SB7.B7_FILIAL = ?
      AND SB7.B7_COD IN ({placeholders})
      AND NULLIF(RTRIM(SB7.B7_DATA), '') IS NOT NULL
    GROUP BY SB7.B7_COD
    """


def last_inventory_dates_batch_sql_scoped(*, branch: str, placeholders: str) -> tuple[str, list]:
    and_sql, params = branch_filter_and("SB7.B7_FILIAL", branch)
    sql = f"""
    SELECT
        RTRIM(SB7.B7_COD) AS product_code,
        MAX(RTRIM(SB7.B7_DATA)) AS last_inventory_date
    FROM SB7010 SB7 WITH (NOLOCK)
    WHERE SB7.D_E_L_E_T_ = ''
      {and_sql}
      AND SB7.B7_COD IN ({placeholders})
      AND NULLIF(RTRIM(SB7.B7_DATA), '') IS NOT NULL
    GROUP BY SB7.B7_COD
    """
    return sql, params


def consumption_monthly_series_sql(
    *,
    branch: str,
    product_param: str = "?",
    start_date_param: str = "?",
) -> tuple[str, list]:
    """Série mensal de consumo (baixas elegíveis) para um produto."""
    and_sql, params = branch_filter_and("RTRIM(SD3.D3_FILIAL)", branch)
    sql = f"""
    SELECT
        LEFT(RTRIM(SD3.D3_EMISSAO), 6) AS year_month,
        SUM(CAST(ISNULL(SD3.D3_QUANT, 0) AS FLOAT)) AS consumption_quantity,
        COUNT(*) AS movement_count
    FROM SD3010 SD3 WITH (NOLOCK)
    WHERE SD3.D_E_L_E_T_ = ''
      {and_sql}
      AND RTRIM(SD3.D3_COD) = {product_param}
      AND RTRIM(SD3.D3_LOCAL) = '{CONSUMPTION_WAREHOUSE}'
      AND LTRIM(RTRIM(ISNULL(SD3.D3_OP, ''))) <> ''
      AND RTRIM(SD3.D3_TM) = '{CONSUMPTION_MOVEMENT_TYPE}'
      AND SD3.D3_EMISSAO >= {start_date_param}
    GROUP BY LEFT(RTRIM(SD3.D3_EMISSAO), 6)
    ORDER BY year_month ASC
    """
    return sql, params
