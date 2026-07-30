"""SQL builders — saldos de estoque por armazém (SB2 × SB1).

Valoração: B2_QATU * B2_CM1 do mesmo B2_LOCAL (controle / Power BI).
Doc: docs/api/supplies-stock-balances.md · padroes-totvs/armazem-custo.md
"""

from __future__ import annotations

from typing import Any

# Expressão canônica de valor de linha (mesmo local).
STOCK_VALUE_EXPR = (
    "CAST(SB2.B2_QATU AS DECIMAL(18, 6)) * CAST(SB2.B2_CM1 AS DECIMAL(18, 6))"
)

SORT_COLUMNS: dict[str, str] = {
    "stock_value_desc": f"({STOCK_VALUE_EXPR}) DESC, SB2.B2_COD ASC",
    "stock_value_asc": f"({STOCK_VALUE_EXPR}) ASC, SB2.B2_COD ASC",
    "quantity_desc": "SB2.B2_QATU DESC, SB2.B2_COD ASC",
    "quantity_asc": "SB2.B2_QATU ASC, SB2.B2_COD ASC",
    "product_code_asc": "SB2.B2_COD ASC",
    "product_code_desc": "SB2.B2_COD DESC",
}

DEFAULT_SORT = "stock_value_desc"


def resolve_order_by(sort: str | None) -> str:
    key = (sort or DEFAULT_SORT).strip().lower()
    return SORT_COLUMNS.get(key, SORT_COLUMNS[DEFAULT_SORT])


def build_where_clause(
    *,
    branch: str | None,
    warehouse: str | None,
    only_positive: bool,
) -> tuple[str, list[Any]]:
    clauses = ["SB2.D_E_L_E_T_ = ''"]
    params: list[Any] = []

    if branch:
        clauses.append("LTRIM(RTRIM(SB2.B2_FILIAL)) = ?")
        params.append(branch.strip())

    if warehouse:
        clauses.append("LTRIM(RTRIM(SB2.B2_LOCAL)) = ?")
        params.append(warehouse.strip())

    if only_positive:
        clauses.append("SB2.B2_QATU > 0")

    return " AND ".join(clauses), params


def format_summary_sql(where_clause: str) -> str:
    return f"""
SELECT
    ISNULL(SUM({STOCK_VALUE_EXPR}), 0) AS total_stock_value,
    ISNULL(SUM(CAST(SB2.B2_QATU AS DECIMAL(18, 6))), 0) AS total_quantity,
    ISNULL(SUM(CAST(SB2.B2_VATU1 AS DECIMAL(18, 6))), 0) AS total_stock_value_vatu1,
    COUNT(DISTINCT SB2.B2_COD) AS product_count,
    COUNT(DISTINCT LTRIM(RTRIM(SB2.B2_LOCAL))) AS warehouse_count
FROM SB2010 SB2 WITH (NOLOCK)
WHERE {where_clause}
""".strip()


def format_by_warehouse_sql(where_clause: str) -> str:
    return f"""
SELECT
    LTRIM(RTRIM(SB2.B2_FILIAL)) AS branch,
    LTRIM(RTRIM(SB2.B2_LOCAL)) AS warehouse,
    COUNT(DISTINCT SB2.B2_COD) AS product_count,
    ISNULL(SUM(CAST(SB2.B2_QATU AS DECIMAL(18, 6))), 0) AS total_quantity,
    ISNULL(SUM({STOCK_VALUE_EXPR}), 0) AS total_stock_value,
    ISNULL(SUM(CAST(SB2.B2_VATU1 AS DECIMAL(18, 6))), 0) AS total_stock_value_vatu1
FROM SB2010 SB2 WITH (NOLOCK)
WHERE {where_clause}
GROUP BY LTRIM(RTRIM(SB2.B2_FILIAL)), LTRIM(RTRIM(SB2.B2_LOCAL))
ORDER BY total_stock_value DESC, warehouse ASC
""".strip()


def format_count_items_sql(where_clause: str) -> str:
    return f"""
SELECT COUNT(*) AS total
FROM SB2010 SB2 WITH (NOLOCK)
WHERE {where_clause}
""".strip()


def format_items_sql(where_clause: str, *, order_by: str) -> str:
    return f"""
SELECT
    LTRIM(RTRIM(SB2.B2_COD)) AS product_code,
    ISNULL(MAX(LTRIM(RTRIM(SB1.B1_DESC))), '') AS description,
    LTRIM(RTRIM(SB2.B2_FILIAL)) AS branch,
    LTRIM(RTRIM(SB2.B2_LOCAL)) AS warehouse,
    CAST(SB2.B2_QATU AS DECIMAL(18, 6)) AS quantity,
    CAST(SB2.B2_CM1 AS DECIMAL(18, 6)) AS unit_cost,
    ({STOCK_VALUE_EXPR}) AS stock_value
FROM SB2010 SB2 WITH (NOLOCK)
LEFT JOIN SB1010 SB1 WITH (NOLOCK)
    ON SB1.D_E_L_E_T_ = ''
   AND SB1.B1_COD = SB2.B2_COD
WHERE {where_clause}
GROUP BY
    SB2.B2_COD,
    SB2.B2_FILIAL,
    SB2.B2_LOCAL,
    SB2.B2_QATU,
    SB2.B2_CM1
ORDER BY {order_by}
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
""".strip()
