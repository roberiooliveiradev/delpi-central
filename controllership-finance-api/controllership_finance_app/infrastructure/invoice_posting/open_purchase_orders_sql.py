from __future__ import annotations

def branch_filter_and(column: str, scope: str) -> tuple[str, list]:
    """Todas → sem predicado; 01/02 → ``AND column = ?``."""
    clause, params = branch_filter_sql(column, scope)
    if not clause:
        return "", []
    return f"AND {clause}", list(params)


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


