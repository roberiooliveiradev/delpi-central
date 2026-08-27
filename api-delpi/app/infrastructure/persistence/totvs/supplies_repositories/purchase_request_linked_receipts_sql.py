"""SQL — incremental purchase receipts (SD1) linked to a PO that is linked to an SC."""

from __future__ import annotations

from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_linked_orders_sql import (
    clamp_linked_orders_limit,
)


def build_recent_linked_receipts_sql(*, limit: int) -> str:
    safe_limit = clamp_linked_orders_limit(limit)
    return f"""
    SELECT TOP {safe_limit}
        CAST(SD1.R_E_C_N_O_ AS BIGINT) AS recno,
        RTRIM(SD1.D1_FILIAL) AS branch,
        RTRIM(SD1.D1_DOC) AS invoice_number,
        RTRIM(SD1.D1_SERIE) AS invoice_series,
        RTRIM(SD1.D1_ITEM) AS invoice_item,
        RTRIM(SD1.D1_PEDIDO) AS order_number,
        RTRIM(SD1.D1_ITEMPC) AS order_item,
        RTRIM(SC7.C7_NUMSC) AS request_number,
        RTRIM(SC7.C7_ITEMSC) AS request_item,
        RTRIM(SD1.D1_COD) AS product_code,
        RTRIM(COALESCE(SB1.B1_DESC, SC7.C7_DESCRI, '')) AS product_description,
        RTRIM(SD1.D1_FORNECE) AS supplier_code,
        RTRIM(COALESCE(SA2.A2_NREDUZ, SA2.A2_NOME, '')) AS supplier_name,
        CAST(ISNULL(SD1.D1_QUANT, 0) AS FLOAT) AS quantity,
        RTRIM(SD1.D1_DTDIGIT) AS entry_date,
        RTRIM(ISNULL(SC1.C1_USER, '')) AS requester_protheus_user_id
    FROM SD1010 SD1 WITH (NOLOCK)
    INNER JOIN SC7010 SC7 WITH (NOLOCK)
        ON SC7.D_E_L_E_T_ = ''
       AND RTRIM(SC7.C7_FILIAL) = RTRIM(SD1.D1_FILIAL)
       AND RTRIM(SC7.C7_NUM) = RTRIM(SD1.D1_PEDIDO)
       AND RTRIM(SC7.C7_ITEM) = RTRIM(SD1.D1_ITEMPC)
       AND RTRIM(SC7.C7_FORNECE) = RTRIM(SD1.D1_FORNECE)
       AND RTRIM(SC7.C7_LOJA) = RTRIM(SD1.D1_LOJA)
       AND RTRIM(SC7.C7_PRODUTO) = RTRIM(SD1.D1_COD)
    INNER JOIN SC1010 SC1 WITH (NOLOCK)
        ON SC1.D_E_L_E_T_ = ''
       AND RTRIM(SC1.C1_FILIAL) = RTRIM(SC7.C7_FILIAL)
       AND RTRIM(SC1.C1_NUM) = RTRIM(SC7.C7_NUMSC)
       AND RTRIM(SC1.C1_ITEM) = RTRIM(SC7.C7_ITEMSC)
    LEFT JOIN SB1010 SB1 WITH (NOLOCK)
        ON SB1.B1_COD = SD1.D1_COD
       AND SB1.D_E_L_E_T_ = ''
    LEFT JOIN SA2010 SA2 WITH (NOLOCK)
        ON SA2.A2_COD = SD1.D1_FORNECE
       AND SA2.A2_LOJA = SD1.D1_LOJA
       AND SA2.D_E_L_E_T_ = ''
    WHERE SD1.D_E_L_E_T_ = ''
      AND RTRIM(ISNULL(SD1.D1_PEDIDO, '')) <> ''
      AND RTRIM(ISNULL(SD1.D1_ITEMPC, '')) <> ''
      AND RTRIM(ISNULL(SC7.C7_NUMSC, '')) <> ''
      AND SD1.R_E_C_N_O_ > ?
    ORDER BY SD1.R_E_C_N_O_
    """


def build_recent_linked_receipts_max_recno_sql() -> str:
    return """
    SELECT CAST(ISNULL(MAX(SD1.R_E_C_N_O_), 0) AS BIGINT) AS max_recno
    FROM SD1010 SD1 WITH (NOLOCK)
    WHERE SD1.D_E_L_E_T_ = ''
      AND RTRIM(ISNULL(SD1.D1_PEDIDO, '')) <> ''
    """
