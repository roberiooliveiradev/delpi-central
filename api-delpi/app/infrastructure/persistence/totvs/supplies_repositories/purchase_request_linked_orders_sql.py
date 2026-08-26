"""SQL — incremental purchase orders newly linked to a purchase request (SC7→SC1)."""

from __future__ import annotations

DEFAULT_LIMIT = 100
MAX_LIMIT = 500


def clamp_linked_orders_limit(limit: int | None) -> int:
    try:
        parsed = int(limit if limit is not None else DEFAULT_LIMIT)
    except (TypeError, ValueError):
        parsed = DEFAULT_LIMIT
    return min(MAX_LIMIT, max(1, parsed))


def normalize_after_recno(after_recno: int | None) -> int:
    try:
        parsed = int(after_recno if after_recno is not None else 0)
    except (TypeError, ValueError):
        parsed = 0
    return max(0, parsed)


def build_recent_linked_orders_sql(*, limit: int) -> str:
    safe_limit = clamp_linked_orders_limit(limit)
    return f"""
    SELECT TOP {safe_limit}
        CAST(SC7.R_E_C_N_O_ AS BIGINT) AS recno,
        RTRIM(SC7.C7_FILIAL) AS branch,
        RTRIM(SC7.C7_NUM) AS order_number,
        RTRIM(SC7.C7_ITEM) AS order_item,
        RTRIM(SC7.C7_NUMSC) AS request_number,
        RTRIM(SC7.C7_ITEMSC) AS request_item,
        RTRIM(SC7.C7_PRODUTO) AS product_code,
        RTRIM(COALESCE(SB1.B1_DESC, SC7.C7_DESCRI, '')) AS product_description,
        RTRIM(SC7.C7_FORNECE) AS supplier_code,
        RTRIM(COALESCE(SA2.A2_NREDUZ, SA2.A2_NOME, '')) AS supplier_name,
        RTRIM(SC7.C7_DATPRF) AS expected_delivery_date,
        RTRIM(ISNULL(SC1.C1_USER, '')) AS requester_protheus_user_id
    FROM SC7010 SC7 WITH (NOLOCK)
    INNER JOIN SC1010 SC1 WITH (NOLOCK)
        ON SC1.D_E_L_E_T_ = ''
       AND RTRIM(SC1.C1_FILIAL) = RTRIM(SC7.C7_FILIAL)
       AND RTRIM(SC1.C1_NUM) = RTRIM(SC7.C7_NUMSC)
       AND RTRIM(SC1.C1_ITEM) = RTRIM(SC7.C7_ITEMSC)
    LEFT JOIN SB1010 SB1 WITH (NOLOCK)
        ON SB1.B1_COD = SC7.C7_PRODUTO
       AND SB1.D_E_L_E_T_ = ''
    LEFT JOIN SA2010 SA2 WITH (NOLOCK)
        ON SA2.A2_COD = SC7.C7_FORNECE
       AND SA2.A2_LOJA = SC7.C7_LOJA
       AND SA2.D_E_L_E_T_ = ''
    WHERE SC7.D_E_L_E_T_ = ''
      AND RTRIM(ISNULL(SC7.C7_NUMSC, '')) <> ''
      AND SC7.R_E_C_N_O_ > ?
    ORDER BY SC7.R_E_C_N_O_
    """


def build_recent_linked_orders_max_recno_sql() -> str:
    return """
    SELECT CAST(ISNULL(MAX(SC7.R_E_C_N_O_), 0) AS BIGINT) AS max_recno
    FROM SC7010 SC7 WITH (NOLOCK)
    WHERE SC7.D_E_L_E_T_ = ''
      AND RTRIM(ISNULL(SC7.C7_NUMSC, '')) <> ''
    """
