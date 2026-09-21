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
