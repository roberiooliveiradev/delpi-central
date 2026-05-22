"""SQL compartilhado para estoque histórico estimado (SB9010 + SD3010)."""

HISTORICAL_STOCK_ITEM_CTES = """
        WITH ultima_data_sb9 AS (
            SELECT
                B9_FILIAL AS branch,
                MAX(B9_DATA) AS closing_base_date
            FROM SB9010
            WHERE D_E_L_E_T_ = ''
              AND B9_DATA <> ''
              AND B9_DATA < ?
              {sb9_branch_filter}
            GROUP BY B9_FILIAL
        ),
        fechamento_base AS (
            SELECT
                B9.B9_FILIAL AS branch,
                RTRIM(B9.B9_LOCAL) AS location,
                RTRIM(B9.B9_COD) AS product_code,
                SUM(B9.B9_QINI) AS closing_base_quantity,
                SUM(B9.B9_VINI1) AS closing_base_value
            FROM SB9010 B9
            INNER JOIN ultima_data_sb9 U
                ON U.branch = B9.B9_FILIAL
               AND U.closing_base_date = B9.B9_DATA
            WHERE B9.D_E_L_E_T_ = ''
              {sb9_branch_filter_b9}
              {sb9_location_filter}
            GROUP BY
                B9.B9_FILIAL,
                RTRIM(B9.B9_LOCAL),
                RTRIM(B9.B9_COD)
        ),
        mov_entre_base_e_inicio AS (
            SELECT
                D3.D3_FILIAL AS branch,
                RTRIM(D3.D3_LOCAL) AS location,
                RTRIM(D3.D3_COD) AS product_code,
                SUM(
                    CASE
                        WHEN D3.D3_TM < '500' THEN D3.D3_QUANT
                        ELSE -D3.D3_QUANT
                    END
                ) AS bridge_quantity,
                SUM(
                    CASE
                        WHEN D3.D3_TM < '500' THEN D3.D3_CUSTO1
                        ELSE -D3.D3_CUSTO1
                    END
                ) AS bridge_value
            FROM SD3010 D3
            INNER JOIN ultima_data_sb9 U
                ON U.branch = D3.D3_FILIAL
            WHERE D3.D_E_L_E_T_ = ''
              AND D3.D3_EMISSAO > U.closing_base_date
              AND D3.D3_EMISSAO < ?
              {d3_branch_filter}
              {d3_location_filter}
            GROUP BY
                D3.D3_FILIAL,
                RTRIM(D3.D3_LOCAL),
                RTRIM(D3.D3_COD)
        ),
        mov_periodo AS (
            SELECT
                D3.D3_FILIAL AS branch,
                RTRIM(D3.D3_LOCAL) AS location,
                RTRIM(D3.D3_COD) AS product_code,
                SUM(
                    CASE
                        WHEN D3.D3_TM < '500' THEN D3.D3_QUANT
                        ELSE -D3.D3_QUANT
                    END
                ) AS period_net_quantity,
                SUM(
                    CASE
                        WHEN D3.D3_TM < '500' THEN D3.D3_CUSTO1
                        ELSE -D3.D3_CUSTO1
                    END
                ) AS period_net_value
            FROM SD3010 D3
            WHERE D3.D_E_L_E_T_ = ''
              AND D3.D3_EMISSAO >= ?
              AND D3.D3_EMISSAO < ?
              {d3_branch_filter}
              {d3_location_filter}
            GROUP BY
                D3.D3_FILIAL,
                RTRIM(D3.D3_LOCAL),
                RTRIM(D3.D3_COD)
        ),
        estoque_item AS (
            SELECT
                COALESCE(FB.branch, MI.branch, MP.branch) AS branch,
                COALESCE(FB.location, MI.location, MP.location) AS location,
                COALESCE(FB.product_code, MI.product_code, MP.product_code) AS product_code,
                COALESCE(FB.closing_base_quantity, 0)
                    + COALESCE(MI.bridge_quantity, 0)
                    + COALESCE(MP.period_net_quantity, 0) AS total_stock_quantity,
                COALESCE(FB.closing_base_value, 0)
                    + COALESCE(MI.bridge_value, 0)
                    + COALESCE(MP.period_net_value, 0) AS total_stock_value
            FROM fechamento_base FB
            FULL OUTER JOIN mov_entre_base_e_inicio MI
                ON MI.branch = FB.branch
               AND MI.location = FB.location
               AND MI.product_code = FB.product_code
            FULL OUTER JOIN mov_periodo MP
                ON MP.branch = COALESCE(FB.branch, MI.branch)
               AND MP.location = COALESCE(FB.location, MI.location)
               AND MP.product_code = COALESCE(FB.product_code, MI.product_code)
        )
"""

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

HISTORICAL_STOCK_SUMMARY_SQL = (
    HISTORICAL_STOCK_ITEM_CTES
    + """
        SELECT
            SUM(total_stock_value) AS total_stock_value,
            SUM(total_stock_quantity) AS total_stock_quantity,
            COUNT(*) AS total_records,
            COUNT(DISTINCT product_code) AS total_products,
            COUNT(DISTINCT location) AS total_locations
        FROM estoque_item
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
