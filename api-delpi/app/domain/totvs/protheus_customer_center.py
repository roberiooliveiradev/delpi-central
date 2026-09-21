"""Product–customer link center (SA7.A7_XCENT).

One center per product + customer + store. The join is a grouped subquery so
repeated SA7 rows with the same center do not multiply fact lines.
"""

from __future__ import annotations

CUSTOMER_CENTER_ALIAS = "SA7C"


def customer_center_link_sql(
    *,
    product_column: str,
    customer_column: str,
    store_column: str,
    alias: str = CUSTOMER_CENTER_ALIAS,
) -> str:
    """INNER JOIN of one non-empty center per product, customer and store."""
    product = product_column.strip()
    customer = customer_column.strip()
    store = store_column.strip()
    link_alias = alias.strip() or CUSTOMER_CENTER_ALIAS
    return f"""
            INNER JOIN (
                SELECT
                    RTRIM(LTRIM(A7_PRODUTO)) AS product_code,
                    RTRIM(LTRIM(A7_CLIENTE)) AS customer_code,
                    RTRIM(LTRIM(A7_LOJA)) AS customer_store,
                    MAX(RTRIM(LTRIM(A7_XCENT))) AS customer_center
                FROM SA7010 WITH (NOLOCK)
                WHERE D_E_L_E_T_ = ''
                  AND RTRIM(ISNULL(A7_XCENT, '')) <> ''
                GROUP BY
                    RTRIM(LTRIM(A7_PRODUTO)),
                    RTRIM(LTRIM(A7_CLIENTE)),
                    RTRIM(LTRIM(A7_LOJA))
            ) {link_alias}
                ON  {link_alias}.product_code = RTRIM(LTRIM({product}))
                AND {link_alias}.customer_code = RTRIM(LTRIM({customer}))
                AND {link_alias}.customer_store = RTRIM(LTRIM({store}))
"""


def customer_center_filter_column(centers: list[str] | None) -> str | None:
    if centers is None:
        return None
    return f"{CUSTOMER_CENTER_ALIAS}.customer_center"


def customer_center_catalog_label(center: str, short_name: str | None) -> str:
    """Display label from the representative store name. Never a hardcoded unit map."""
    code = (center or "").strip()
    name = (short_name or "").strip() or code
    if not code:
        return name
    return f"{name} ({code})"


def customer_center_catalog_sql(*, customer_code_filter_sql: str) -> str:
    """Distinct non-empty centers. One representative short name per center."""
    predicate = (customer_code_filter_sql or "1 = 1").strip() or "1 = 1"
    return f"""
        SELECT
            RTRIM(LTRIM(A7.A7_XCENT)) AS center,
            MIN(
                COALESCE(
                    NULLIF(RTRIM(SA1.A1_NREDUZ), ''),
                    NULLIF(RTRIM(SA1.A1_NOME), ''),
                    RTRIM(LTRIM(A7.A7_XCENT))
                )
            ) AS short_name
        FROM SA7010 A7 WITH (NOLOCK)
        LEFT JOIN SA1010 SA1 WITH (NOLOCK)
            ON  SA1.D_E_L_E_T_ = ''
            AND RTRIM(LTRIM(SA1.A1_COD)) = RTRIM(LTRIM(A7.A7_CLIENTE))
            AND RTRIM(LTRIM(SA1.A1_LOJA)) = RTRIM(LTRIM(A7.A7_LOJA))
        WHERE A7.D_E_L_E_T_ = ''
          AND RTRIM(ISNULL(A7.A7_XCENT, '')) <> ''
          AND ({predicate})
        GROUP BY RTRIM(LTRIM(A7.A7_XCENT))
        ORDER BY center
    """


def customer_center_join_sql(
    *,
    centers: list[str] | None,
    product_column: str,
    customer_column: str,
    store_column: str,
) -> str:
    if not centers:
        return ""
    return customer_center_link_sql(
        product_column=product_column,
        customer_column=customer_column,
        store_column=store_column,
    ).rstrip()
