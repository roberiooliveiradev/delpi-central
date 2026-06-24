"""SQL compartilhado para estoque histórico estimado (SB9010 + SD3010)."""

from dataclasses import dataclass

_SD3_NET_QUANT = """
                    CASE
                        WHEN D3.D3_TM < '500' THEN D3.D3_QUANT
                        ELSE -D3.D3_QUANT
                    END"""

_SD3_NET_VALUE = """
                    CASE
                        WHEN D3.D3_TM < '500' THEN D3.D3_CUSTO1
                        ELSE -D3.D3_CUSTO1
                    END"""

HISTORICAL_STOCK_BASE_CTES = f"""
        WITH ultima_data_sb9 AS (
            SELECT
                B9_FILIAL AS branch,
                MAX(B9_DATA) AS closing_base_date
            FROM SB9010 WITH (NOLOCK)
            WHERE D_E_L_E_T_ = ''
              AND B9_DATA <> ''
              AND B9_DATA < ?
              {{sb9_branch_filter}}
            GROUP BY B9_FILIAL
        ),
        fechamento_base AS (
            SELECT
                B9.B9_FILIAL AS branch,
                RTRIM(B9.B9_LOCAL) AS location,
                RTRIM(B9.B9_COD) AS product_code,
                SUM(B9.B9_QINI) AS closing_base_quantity,
                SUM(B9.B9_VINI1) AS closing_base_value
            FROM SB9010 B9 WITH (NOLOCK)
            INNER JOIN ultima_data_sb9 U
                ON U.branch = B9.B9_FILIAL
               AND U.closing_base_date = B9.B9_DATA
            WHERE B9.D_E_L_E_T_ = ''
              {{sb9_branch_filter_b9}}
              {{sb9_location_filter}}
            GROUP BY
                B9.B9_FILIAL,
                RTRIM(B9.B9_LOCAL),
                RTRIM(B9.B9_COD)
        ),
        movimentos_sd3 AS (
            SELECT
                D3.D3_FILIAL AS branch,
                RTRIM(D3.D3_LOCAL) AS location,
                RTRIM(D3.D3_COD) AS product_code,
                SUM(
                    CASE
                        WHEN D3.D3_EMISSAO > U.closing_base_date
                         AND D3.D3_EMISSAO < ?
                        THEN {_SD3_NET_QUANT}
                        ELSE 0
                    END
                ) AS bridge_quantity,
                SUM(
                    CASE
                        WHEN D3.D3_EMISSAO > U.closing_base_date
                         AND D3.D3_EMISSAO < ?
                        THEN {_SD3_NET_VALUE}
                        ELSE 0
                    END
                ) AS bridge_value,
                SUM(
                    CASE
                        WHEN D3.D3_EMISSAO >= ?
                         AND D3.D3_EMISSAO < ?
                        THEN {_SD3_NET_QUANT}
                        ELSE 0
                    END
                ) AS period_net_quantity,
                SUM(
                    CASE
                        WHEN D3.D3_EMISSAO >= ?
                         AND D3.D3_EMISSAO < ?
                        THEN {_SD3_NET_VALUE}
                        ELSE 0
                    END
                ) AS period_net_value
            FROM SD3010 D3 WITH (NOLOCK)
            INNER JOIN ultima_data_sb9 U
                ON U.branch = D3.D3_FILIAL
            WHERE D3.D_E_L_E_T_ = ''
              AND D3.D3_EMISSAO > U.closing_base_date
              AND D3.D3_EMISSAO < ?
              {{d3_branch_filter}}
              {{d3_location_filter}}
            GROUP BY
                D3.D3_FILIAL,
                RTRIM(D3.D3_LOCAL),
                RTRIM(D3.D3_COD)
        )
"""

HISTORICAL_STOCK_META_CTES = """,
        branch_breakdown AS (
            SELECT
                U.branch,
                U.closing_base_date,
                COALESCE(FB.closing_base_value, 0) AS closing_base_value,
                COALESCE(M.bridge_value, 0) AS bridge_value,
                COALESCE(M.period_net_value, 0) AS period_net_value
            FROM ultima_data_sb9 U
            LEFT JOIN (
                SELECT branch, SUM(closing_base_value) AS closing_base_value
                FROM fechamento_base
                GROUP BY branch
            ) FB
                ON FB.branch = U.branch
            LEFT JOIN (
                SELECT
                    branch,
                    SUM(bridge_value) AS bridge_value,
                    SUM(period_net_value) AS period_net_value
                FROM movimentos_sd3
                GROUP BY branch
            ) M
                ON M.branch = U.branch
        ),
        official_closure_latest AS (
            SELECT
                B9.B9_FILIAL AS branch,
                MAX(B9.B9_DATA) AS official_closure_date
            FROM SB9010 B9 WITH (NOLOCK)
            WHERE B9.D_E_L_E_T_ = ''
              AND B9.B9_DATA <> ''
              AND B9.B9_DATA <= ?
              {sb9_branch_filter_official}
            GROUP BY B9.B9_FILIAL
        ),
        official_closure_values AS (
            SELECT
                L.branch,
                L.official_closure_date,
                SUM(B9.B9_VINI1) AS official_closure_value
            FROM official_closure_latest L
            INNER JOIN SB9010 B9 WITH (NOLOCK)
                ON B9.B9_FILIAL = L.branch
               AND B9.B9_DATA = L.official_closure_date
               AND B9.D_E_L_E_T_ = ''
            GROUP BY L.branch, L.official_closure_date
        )
"""

HISTORICAL_STOCK_BRANCH_BREAKDOWN_SELECT = """
        SELECT
            B.branch,
            B.closing_base_date,
            B.closing_base_value,
            B.bridge_value,
            B.period_net_value,
            O.official_closure_date,
            O.official_closure_value,
            CASE
                WHEN O.official_closure_date IS NOT NULL
                 AND RTRIM(O.official_closure_date) <> ''
                THEN 1
                ELSE 0
            END AS official_closure_available,
            CASE
                WHEN O.official_closure_date = ?
                THEN 1
                ELSE 0
            END AS official_closure_on_period_end
        FROM branch_breakdown B
        LEFT JOIN official_closure_values O
            ON O.branch = B.branch
        ORDER BY B.branch
"""

HISTORICAL_STOCK_ESTOQUE_ITEM_CTES = """,
        item_keys AS (
            SELECT branch, location, product_code FROM fechamento_base
            UNION
            SELECT branch, location, product_code FROM movimentos_sd3
        ),
        estoque_item AS (
            SELECT
                K.branch,
                K.location,
                K.product_code,
                COALESCE(FB.closing_base_quantity, 0)
                    + COALESCE(M.bridge_quantity, 0)
                    + COALESCE(M.period_net_quantity, 0) AS total_stock_quantity,
                COALESCE(FB.closing_base_value, 0)
                    + COALESCE(M.bridge_value, 0)
                    + COALESCE(M.period_net_value, 0) AS total_stock_value
            FROM item_keys K
            LEFT JOIN fechamento_base FB
                ON FB.branch = K.branch
               AND FB.location = K.location
               AND FB.product_code = K.product_code
            LEFT JOIN movimentos_sd3 M
                ON M.branch = K.branch
               AND M.location = K.location
               AND M.product_code = K.product_code
        )
"""

HISTORICAL_STOCK_SUMMARY_ROLLUP_CTES = """,
        item_totals AS (
            SELECT
                branch,
                location,
                product_code,
                SUM(part_quantity) AS total_stock_quantity,
                SUM(part_value) AS total_stock_value
            FROM (
                SELECT
                    branch,
                    location,
                    product_code,
                    closing_base_quantity AS part_quantity,
                    closing_base_value AS part_value
                FROM fechamento_base
                UNION ALL
                SELECT
                    branch,
                    location,
                    product_code,
                    bridge_quantity + period_net_quantity,
                    bridge_value + period_net_value
                FROM movimentos_sd3
            ) parts
            GROUP BY branch, location, product_code
        )
"""

HISTORICAL_STOCK_SUMMARY_SQL = (
    HISTORICAL_STOCK_BASE_CTES
    + HISTORICAL_STOCK_SUMMARY_ROLLUP_CTES
    + """
        SELECT
            SUM(total_stock_value) AS total_stock_value,
            SUM(total_stock_quantity) AS total_stock_quantity,
            COUNT(*) AS total_records,
            COUNT(DISTINCT product_code) AS total_products,
            COUNT(DISTINCT location) AS total_locations
        FROM item_totals
    """
)

HISTORICAL_STOCK_BREAKDOWN_ONLY_SQL = (
    HISTORICAL_STOCK_BASE_CTES
    + HISTORICAL_STOCK_META_CTES
    + HISTORICAL_STOCK_BRANCH_BREAKDOWN_SELECT
)

HISTORICAL_STOCK_ITEM_CTES = HISTORICAL_STOCK_BASE_CTES + HISTORICAL_STOCK_ESTOQUE_ITEM_CTES

HISTORICAL_STOCK_BY_BRANCH_SQL = (
    HISTORICAL_STOCK_ITEM_CTES
    + """
        SELECT
            branch,
            SUM(total_stock_value) AS total_stock_value,
            SUM(total_stock_quantity) AS total_stock_quantity,
            COUNT(*) AS total_records,
            COUNT(DISTINCT product_code) AS total_products,
            COUNT(DISTINCT location) AS total_locations
        FROM estoque_item
        GROUP BY branch
        ORDER BY branch
    """
)

HISTORICAL_STOCK_BY_LOCATION_SQL = (
    HISTORICAL_STOCK_ITEM_CTES
    + """
        SELECT
            branch,
            location,
            SUM(total_stock_value) AS total_stock_value,
            SUM(total_stock_quantity) AS total_stock_quantity,
            COUNT(*) AS total_records,
            COUNT(DISTINCT product_code) AS total_products
        FROM estoque_item
        GROUP BY branch, location
        ORDER BY branch, location
    """
)

HISTORICAL_STOCK_TOP_PRODUCTS_SQL = (
    HISTORICAL_STOCK_ITEM_CTES
    + """
        SELECT TOP {limit}
            ranked.product_code,
            MAX(SB1.B1_DESC) AS product_description,
            SUM(ranked.total_stock_value) AS total_stock_value,
            SUM(ranked.total_stock_quantity) AS total_stock_quantity,
            COUNT(DISTINCT ranked.location) AS total_locations
        FROM estoque_item ranked
        LEFT JOIN SB1010 SB1
            ON SB1.D_E_L_E_T_ = ''
           AND SB1.B1_COD = ranked.product_code
        GROUP BY ranked.product_code
        HAVING SUM(ranked.total_stock_value) <> 0
            OR SUM(ranked.total_stock_quantity) <> 0
        ORDER BY total_stock_value DESC, ranked.product_code
    """
)

HISTORICAL_STOCK_TEMP_TABLE = "#Delpi_StockItems"

_HISTORICAL_STOCK_BUNDLE_FROM_TEMP = (
    """
        SELECT
            SUM(total_stock_value) AS total_stock_value,
            SUM(total_stock_quantity) AS total_stock_quantity,
            COUNT(*) AS total_records,
            COUNT(DISTINCT product_code) AS total_products,
            COUNT(DISTINCT location) AS total_locations
        FROM """
    + HISTORICAL_STOCK_TEMP_TABLE
    + """;

        SELECT
            branch,
            SUM(total_stock_value) AS total_stock_value,
            SUM(total_stock_quantity) AS total_stock_quantity,
            COUNT(*) AS total_records,
            COUNT(DISTINCT product_code) AS total_products,
            COUNT(DISTINCT location) AS total_locations
        FROM """
    + HISTORICAL_STOCK_TEMP_TABLE
    + """
        GROUP BY branch
        ORDER BY branch;

        SELECT
            branch,
            location,
            SUM(total_stock_value) AS total_stock_value,
            SUM(total_stock_quantity) AS total_stock_quantity,
            COUNT(*) AS total_records,
            COUNT(DISTINCT product_code) AS total_products
        FROM """
    + HISTORICAL_STOCK_TEMP_TABLE
    + """
        GROUP BY branch, location
        ORDER BY branch, location;

        SELECT TOP {limit}
            ranked.product_code,
            MAX(SB1.B1_DESC) AS product_description,
            SUM(ranked.total_stock_value) AS total_stock_value,
            SUM(ranked.total_stock_quantity) AS total_stock_quantity,
            COUNT(DISTINCT ranked.location) AS total_locations
        FROM """
    + HISTORICAL_STOCK_TEMP_TABLE
    + """ ranked
        LEFT JOIN SB1010 SB1
            ON SB1.D_E_L_E_T_ = ''
           AND SB1.B1_COD = ranked.product_code
        GROUP BY ranked.product_code
        HAVING SUM(ranked.total_stock_value) <> 0
            OR SUM(ranked.total_stock_quantity) <> 0
        ORDER BY total_stock_value DESC, ranked.product_code;
    """
)

HISTORICAL_STOCK_BUNDLE_BATCH_SQL = (
    """
        SET NOCOUNT ON;
        DROP TABLE IF EXISTS """
    + HISTORICAL_STOCK_TEMP_TABLE
    + """;
        """
    + HISTORICAL_STOCK_ITEM_CTES
    + """
        SELECT
            branch,
            location,
            product_code,
            total_stock_quantity,
            total_stock_value
        INTO """
    + HISTORICAL_STOCK_TEMP_TABLE
    + """
        FROM estoque_item;
        SET NOCOUNT OFF;

        """
    + _HISTORICAL_STOCK_BUNDLE_FROM_TEMP
)


@dataclass(frozen=True)
class HistoricalStockFilterClauses:
    sb9_branch_filter: str
    sb9_branch_filter_b9: str
    sb9_branch_filter_official: str
    sb9_location_filter: str
    d3_branch_filter: str
    d3_location_filter: str


def format_historical_stock_sql(
    *,
    summary_only: bool,
    filters: HistoricalStockFilterClauses,
    top_limit: int = 10,
) -> str:
    placeholders = {
        "sb9_branch_filter": filters.sb9_branch_filter,
        "sb9_branch_filter_b9": filters.sb9_branch_filter_b9,
        "sb9_branch_filter_official": filters.sb9_branch_filter_official,
        "sb9_location_filter": filters.sb9_location_filter,
        "d3_branch_filter": filters.d3_branch_filter,
        "d3_location_filter": filters.d3_location_filter,
        "limit": max(1, int(top_limit or 10)),
    }
    template = (
        HISTORICAL_STOCK_SUMMARY_SQL
        if summary_only
        else HISTORICAL_STOCK_BUNDLE_BATCH_SQL
    )
    return template.format(**placeholders)


def format_historical_breakdown_sql(*, filters: HistoricalStockFilterClauses) -> str:
    placeholders = {
        "sb9_branch_filter": filters.sb9_branch_filter,
        "sb9_branch_filter_b9": filters.sb9_branch_filter_b9,
        "sb9_branch_filter_official": filters.sb9_branch_filter_official,
        "sb9_location_filter": filters.sb9_location_filter,
        "d3_branch_filter": filters.d3_branch_filter,
        "d3_location_filter": filters.d3_location_filter,
    }
    return HISTORICAL_STOCK_BREAKDOWN_ONLY_SQL.format(**placeholders)


def build_historical_stock_params(
    *,
    period_start: str,
    period_end: str,
    period_end_exclusive: str,
    sb9_params: tuple,
    sb9_b9_params: tuple,
    sb9_official_params: tuple,
    sb9_loc_params: tuple,
    d3_params: tuple,
    d3_loc_params: tuple,
    include_breakdown_select: bool = False,
) -> tuple:
    """Ordem alinhada aos placeholders do SQL histórico compartilhado."""
    movement_dates = (
        period_start,
        period_start,
        period_start,
        period_end_exclusive,
        period_start,
        period_end_exclusive,
        period_end_exclusive,
    )
    movement_tail = movement_dates + d3_params + d3_loc_params
    if include_breakdown_select:
        return (
            (period_start,)
            + sb9_params
            + sb9_b9_params
            + sb9_loc_params
            + movement_tail
            + (period_end,)
            + sb9_official_params
            + (period_end,)
        )
    return (period_start,) + sb9_params + sb9_b9_params + sb9_loc_params + movement_tail
