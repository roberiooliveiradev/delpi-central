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
    join_type: str = "inner",
) -> str:
    """Grouped SA7 join. ``left`` projects the center; ``inner`` keeps the filter join."""
    product = product_column.strip()
    customer = customer_column.strip()
    store = store_column.strip()
    link_alias = alias.strip() or CUSTOMER_CENTER_ALIAS
    keyword = "LEFT JOIN" if str(join_type or "").strip().lower() == "left" else "INNER JOIN"
    return f"""
            {keyword} (
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


def customer_center_assignments_sql(*, customer_code_filter_sql: str) -> str:
    """One row per customer, store and non-empty center. No hardcoded center list."""
    predicate = (customer_code_filter_sql or "1 = 1").strip() or "1 = 1"
    return f"""
        SELECT
            RTRIM(LTRIM(A7.A7_CLIENTE)) AS customer_code,
            RTRIM(LTRIM(A7.A7_LOJA)) AS customer_store,
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
        GROUP BY
            RTRIM(LTRIM(A7.A7_CLIENTE)),
            RTRIM(LTRIM(A7.A7_LOJA)),
            RTRIM(LTRIM(A7.A7_XCENT))
        ORDER BY customer_code, customer_store, center
    """


def customer_center_in_predicate(centers: list[str] | None) -> tuple[str, list[str]]:
    """Predicate on ``SA7C.customer_center``. Blank SQL when the filter is absent."""
    if centers is None:
        return "", []
    if not centers:
        return "1 = 0", []
    placeholders = ", ".join("?" for _ in centers)
    return f"RTRIM({CUSTOMER_CENTER_ALIAS}.customer_center) IN ({placeholders})", list(centers)


def customer_center_exists_predicate(
    centers: list[str] | None,
    *,
    product_column: str = "D2.D2_COD",
    customer_column: str = "D2.D2_CLIENTE",
    store_column: str = "D2.D2_LOJA",
) -> tuple[str, list[str]]:
    """EXISTS against the grouped link. Empty SQL when the filter is absent."""
    if centers is None:
        return "", []
    if not centers:
        return "1 = 0", []
    placeholders = ", ".join("?" for _ in centers)
    sql = f"""
        EXISTS (
            SELECT 1
            FROM (
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
            ) {CUSTOMER_CENTER_ALIAS}
            WHERE {CUSTOMER_CENTER_ALIAS}.product_code = RTRIM(LTRIM({product_column}))
              AND {CUSTOMER_CENTER_ALIAS}.customer_code = RTRIM(LTRIM({customer_column}))
              AND {CUSTOMER_CENTER_ALIAS}.customer_store = RTRIM(LTRIM({store_column}))
              AND RTRIM({CUSTOMER_CENTER_ALIAS}.customer_center) IN ({placeholders})
        )
    """
    return sql, list(centers)


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
