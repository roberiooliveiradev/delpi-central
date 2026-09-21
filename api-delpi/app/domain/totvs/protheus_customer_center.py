"""Product–customer link center (SA7.A7_XCENT) and master ZC0.

One center per product + customer + store. Joins are grouped subqueries so
repeated SA7/ZC0 rows with the same key do not multiply fact lines.

Classification uses the **current** SA7/ZC0 snapshot. Historical invoices are
not frozen; a later A7_XCENT change reclassifies past billing.

SA7 and ZC0 are treated as shared dictionaries: the grouped subquery does not
filter ``A7_FILIAL`` / ``ZC0_FILIAL``. That matches the live Protheus setup
(empty branch on shared tables) and the existing SA7 filter fragment.
"""

from __future__ import annotations

CUSTOMER_CENTER_ALIAS = "SA7C"
CUSTOMER_CENTER_MASTER_ALIAS = "ZC0"
UNCLASSIFIED_CUSTOMER_CENTER_NAME = "SEM CENTRO"


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


def customer_center_classification_join_sql(
    *,
    product_column: str,
    customer_column: str,
    store_column: str,
    alias: str = CUSTOMER_CENTER_ALIAS,
) -> str:
    """LEFT JOIN of the current SA7 center, including empty/missing links.

    Empty ``A7_XCENT`` becomes NULL so the fact line stays in the result as
    unclassified (``SEM CENTRO``).
    """
    product = product_column.strip()
    customer = customer_column.strip()
    store = store_column.strip()
    link_alias = alias.strip() or CUSTOMER_CENTER_ALIAS
    return f"""
            LEFT JOIN (
                SELECT
                    RTRIM(LTRIM(A7_PRODUTO)) AS product_code,
                    RTRIM(LTRIM(A7_CLIENTE)) AS customer_code,
                    RTRIM(LTRIM(A7_LOJA)) AS customer_store,
                    MAX(NULLIF(RTRIM(LTRIM(A7_XCENT)), '')) AS customer_center
                FROM SA7010 WITH (NOLOCK)
                WHERE D_E_L_E_T_ = ''
                GROUP BY
                    RTRIM(LTRIM(A7_PRODUTO)),
                    RTRIM(LTRIM(A7_CLIENTE)),
                    RTRIM(LTRIM(A7_LOJA))
            ) {link_alias}
                ON  {link_alias}.product_code = RTRIM(LTRIM({product}))
                AND {link_alias}.customer_code = RTRIM(LTRIM({customer}))
                AND {link_alias}.customer_store = RTRIM(LTRIM({store}))
"""


def customer_center_master_join_sql(
    *,
    center_alias: str = CUSTOMER_CENTER_ALIAS,
    alias: str = CUSTOMER_CENTER_MASTER_ALIAS,
) -> str:
    """LEFT JOIN of ZC0 keyed by customer + store + center code.

    Never join ZC0 by center code alone: the code belongs to a customer/store.
    """
    sa7_alias = center_alias.strip() or CUSTOMER_CENTER_ALIAS
    zc0_alias = alias.strip() or CUSTOMER_CENTER_MASTER_ALIAS
    return f"""
            LEFT JOIN (
                SELECT
                    RTRIM(LTRIM(ZC0_CLIENT)) AS customer_code,
                    RTRIM(LTRIM(ZC0_LOJA)) AS customer_store,
                    RTRIM(LTRIM(ZC0_CODIGO)) AS customer_center,
                    MAX(RTRIM(LTRIM(ZC0_DESC))) AS customer_center_name,
                    MAX(RTRIM(LTRIM(ISNULL(ZC0_ATIVO, '')))) AS center_active
                FROM ZC0010 WITH (NOLOCK)
                WHERE D_E_L_E_T_ = ''
                GROUP BY
                    RTRIM(LTRIM(ZC0_CLIENT)),
                    RTRIM(LTRIM(ZC0_LOJA)),
                    RTRIM(LTRIM(ZC0_CODIGO))
            ) {zc0_alias}
                ON  {zc0_alias}.customer_code = {sa7_alias}.customer_code
                AND {zc0_alias}.customer_store = {sa7_alias}.customer_store
                AND {zc0_alias}.customer_center = {sa7_alias}.customer_center
"""


def customer_center_code_expr(
    *,
    center_alias: str = CUSTOMER_CENTER_ALIAS,
) -> str:
    sa7_alias = center_alias.strip() or CUSTOMER_CENTER_ALIAS
    return f"NULLIF(RTRIM(LTRIM(ISNULL({sa7_alias}.customer_center, ''))), '')"


def customer_center_name_expr(
    *,
    center_alias: str = CUSTOMER_CENTER_ALIAS,
    master_alias: str = CUSTOMER_CENTER_MASTER_ALIAS,
    unclassified_name: str = UNCLASSIFIED_CUSTOMER_CENTER_NAME,
) -> str:
    code = customer_center_code_expr(center_alias=center_alias)
    zc0_alias = master_alias.strip() or CUSTOMER_CENTER_MASTER_ALIAS
    sa7_alias = center_alias.strip() or CUSTOMER_CENTER_ALIAS
    literal = unclassified_name.replace("'", "''")
    return (
        f"CASE WHEN {code} IS NULL THEN '{literal}' "
        f"ELSE COALESCE("
        f"NULLIF(RTRIM(LTRIM(ISNULL({zc0_alias}.customer_center_name, ''))), ''), "
        f"RTRIM(LTRIM({sa7_alias}.customer_center))"
        f") END"
    )


def customer_center_active_expr(
    *,
    center_alias: str = CUSTOMER_CENTER_ALIAS,
    master_alias: str = CUSTOMER_CENTER_MASTER_ALIAS,
) -> str:
    """1 = ZC0 active (S/1); 0 = missing or inactive ZC0; NULL = unclassified."""
    code = customer_center_code_expr(center_alias=center_alias)
    zc0_alias = master_alias.strip() or CUSTOMER_CENTER_MASTER_ALIAS
    return (
        f"CASE WHEN {code} IS NULL THEN NULL "
        f"WHEN UPPER(RTRIM(LTRIM(ISNULL({zc0_alias}.center_active, '')))) "
        f"IN ('S', '1') THEN 1 ELSE 0 END"
    )
