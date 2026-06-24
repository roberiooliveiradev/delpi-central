"""SQL para estoque histórico via fechamento oficial SB9010 na data final do período."""

from dataclasses import dataclass

OFFICIAL_CLOSURE_ITEM_CTES = """
        WITH closure_items AS (
            SELECT
                B9.B9_FILIAL AS branch,
                RTRIM(B9.B9_LOCAL) AS location,
                RTRIM(B9.B9_COD) AS product_code,
                SUM(B9.B9_QINI) AS total_stock_quantity,
                SUM(B9.B9_VINI1) AS total_stock_value
            FROM SB9010 B9 WITH (NOLOCK)
            WHERE B9.D_E_L_E_T_ = ''
              AND B9.B9_DATA = ?
              {sb9_branch_filter_b9}
              {sb9_location_filter}
            GROUP BY
                B9.B9_FILIAL,
                RTRIM(B9.B9_LOCAL),
                RTRIM(B9.B9_COD)
        )
"""

OFFICIAL_CLOSURE_SUMMARY_SQL = (
    OFFICIAL_CLOSURE_ITEM_CTES
    + """
        SELECT
            SUM(total_stock_value) AS total_stock_value,
            SUM(total_stock_quantity) AS total_stock_quantity,
            COUNT(*) AS total_records,
            COUNT(DISTINCT product_code) AS total_products,
            COUNT(DISTINCT location) AS total_locations
        FROM closure_items
    """
)

OFFICIAL_CLOSURE_TEMP_TABLE = "#Delpi_OfficialStockItems"

_OFFICIAL_CLOSURE_BUNDLE_FROM_TEMP = (
    """
        SELECT
            SUM(total_stock_value) AS total_stock_value,
            SUM(total_stock_quantity) AS total_stock_quantity,
            COUNT(*) AS total_records,
            COUNT(DISTINCT product_code) AS total_products,
            COUNT(DISTINCT location) AS total_locations
        FROM """
    + OFFICIAL_CLOSURE_TEMP_TABLE
    + """;

        SELECT
            branch,
            SUM(total_stock_value) AS total_stock_value,
            SUM(total_stock_quantity) AS total_stock_quantity,
            COUNT(*) AS total_records,
            COUNT(DISTINCT product_code) AS total_products,
            COUNT(DISTINCT location) AS total_locations
        FROM """
    + OFFICIAL_CLOSURE_TEMP_TABLE
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
    + OFFICIAL_CLOSURE_TEMP_TABLE
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
    + OFFICIAL_CLOSURE_TEMP_TABLE
    + """ ranked
        LEFT JOIN SB1010 SB1 WITH (NOLOCK)
            ON SB1.D_E_L_E_T_ = ''
           AND SB1.B1_COD = ranked.product_code
        GROUP BY ranked.product_code
        HAVING SUM(ranked.total_stock_value) <> 0
            OR SUM(ranked.total_stock_quantity) <> 0
        ORDER BY total_stock_value DESC, ranked.product_code;
    """
)

OFFICIAL_CLOSURE_BUNDLE_BATCH_SQL = (
    """
        SET NOCOUNT ON;
        DROP TABLE IF EXISTS """
    + OFFICIAL_CLOSURE_TEMP_TABLE
    + """;
        """
    + OFFICIAL_CLOSURE_ITEM_CTES
    + """
        SELECT
            branch,
            location,
            product_code,
            total_stock_quantity,
            total_stock_value
        INTO """
    + OFFICIAL_CLOSURE_TEMP_TABLE
    + """
        FROM closure_items;
        SET NOCOUNT OFF;

        """
    + _OFFICIAL_CLOSURE_BUNDLE_FROM_TEMP
)


@dataclass(frozen=True)
class OfficialClosureFilterClauses:
    sb9_branch_filter_b9: str
    sb9_location_filter: str


def format_official_closure_sql(
    *,
    summary_only: bool,
    filters: OfficialClosureFilterClauses,
    top_limit: int = 10,
) -> str:
    placeholders = {
        "sb9_branch_filter_b9": filters.sb9_branch_filter_b9,
        "sb9_location_filter": filters.sb9_location_filter,
        "limit": max(1, int(top_limit or 10)),
    }
    template = (
        OFFICIAL_CLOSURE_SUMMARY_SQL
        if summary_only
        else OFFICIAL_CLOSURE_BUNDLE_BATCH_SQL
    )
    return template.format(**placeholders)


def build_official_closure_params(
    *,
    period_end: str,
    sb9_b9_params: tuple,
    sb9_loc_params: tuple,
) -> tuple:
    return (period_end,) + sb9_b9_params + sb9_loc_params
