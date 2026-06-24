/*
  W0 — Reconciliação estoque Suprimentos vs. inventário oficial (SB9/SB2/SD3).

  Ajuste as datas abaixo ou use reconcile_stock_value.py (substitui via script).

  Result sets (ordem):
    1) estimated_by_branch     — espelha GET /supplies/stock-value (SB9 base + SD3)
    2) official_closure_le_end — MAX(B9_DATA) <= end_date por filial
    3) official_closure_on_end — fechamento exato em end_date (data do inventário)
    4) sb2_current             — saldo corrente SB2
    5) recent_sb9_dates        — últimas datas SB9 por filial (auditoria)
*/
SET NOCOUNT ON;

DECLARE @start_date CHAR(8) = '20260501';
DECLARE @end_date CHAR(8) = '20260531';
DECLARE @end_exclusive CHAR(8) = '20260601';

-- (1) Estimativa API — breakdown por filial
WITH ultima_data_sb9 AS (
    SELECT
        B9_FILIAL AS branch,
        MAX(B9_DATA) AS closing_base_date
    FROM SB9010 WITH (NOLOCK)
    WHERE D_E_L_E_T_ = ''
      AND B9_DATA <> ''
      AND B9_DATA < @start_date
      AND B9_FILIAL IN ('01', '02')
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
      AND B9.B9_FILIAL IN ('01', '02')
    GROUP BY B9.B9_FILIAL, RTRIM(B9.B9_LOCAL), RTRIM(B9.B9_COD)
),
movimentos_sd3 AS (
    SELECT
        D3.D3_FILIAL AS branch,
        RTRIM(D3.D3_LOCAL) AS location,
        RTRIM(D3.D3_COD) AS product_code,
        SUM(
            CASE
                WHEN D3.D3_EMISSAO > U.closing_base_date
                 AND D3.D3_EMISSAO < @start_date
                THEN CASE WHEN D3.D3_TM < '500' THEN D3.D3_QUANT ELSE -D3.D3_QUANT END
                ELSE 0
            END
        ) AS bridge_quantity,
        SUM(
            CASE
                WHEN D3.D3_EMISSAO > U.closing_base_date
                 AND D3.D3_EMISSAO < @start_date
                THEN CASE WHEN D3.D3_TM < '500' THEN D3.D3_CUSTO1 ELSE -D3.D3_CUSTO1 END
                ELSE 0
            END
        ) AS bridge_value,
        SUM(
            CASE
                WHEN D3.D3_EMISSAO >= @start_date
                 AND D3.D3_EMISSAO < @end_exclusive
                THEN CASE WHEN D3.D3_TM < '500' THEN D3.D3_QUANT ELSE -D3.D3_QUANT END
                ELSE 0
            END
        ) AS period_net_quantity,
        SUM(
            CASE
                WHEN D3.D3_EMISSAO >= @start_date
                 AND D3.D3_EMISSAO < @end_exclusive
                THEN CASE WHEN D3.D3_TM < '500' THEN D3.D3_CUSTO1 ELSE -D3.D3_CUSTO1 END
                ELSE 0
            END
        ) AS period_net_value
    FROM SD3010 D3 WITH (NOLOCK)
    INNER JOIN ultima_data_sb9 U
        ON U.branch = D3.D3_FILIAL
    WHERE D3.D_E_L_E_T_ = ''
      AND D3.D3_EMISSAO > U.closing_base_date
      AND D3.D3_EMISSAO < @end_exclusive
      AND D3.D3_FILIAL IN ('01', '02')
    GROUP BY D3.D3_FILIAL, RTRIM(D3.D3_LOCAL), RTRIM(D3.D3_COD)
),
item_totals AS (
    SELECT
        branch,
        location,
        product_code,
        SUM(part_quantity) AS total_stock_quantity,
        SUM(part_value) AS total_stock_value
    FROM (
        SELECT branch, location, product_code,
               closing_base_quantity AS part_quantity,
               closing_base_value AS part_value
        FROM fechamento_base
        UNION ALL
        SELECT branch, location, product_code,
               bridge_quantity + period_net_quantity,
               bridge_value + period_net_value
        FROM movimentos_sd3
    ) parts
    GROUP BY branch, location, product_code
),
estimated_roll AS (
    SELECT
        U.branch,
        U.closing_base_date,
        SUM(COALESCE(FB.closing_base_value, 0)) AS closing_base_value,
        SUM(COALESCE(M.bridge_value, 0)) AS bridge_value,
        SUM(COALESCE(M.period_net_value, 0)) AS period_net_value
    FROM ultima_data_sb9 U
    LEFT JOIN (
        SELECT branch, SUM(closing_base_value) AS closing_base_value
        FROM fechamento_base
        GROUP BY branch
    ) FB ON FB.branch = U.branch
    LEFT JOIN (
        SELECT branch, SUM(bridge_value) AS bridge_value, SUM(period_net_value) AS period_net_value
        FROM movimentos_sd3
        GROUP BY branch
    ) M ON M.branch = U.branch
    GROUP BY U.branch, U.closing_base_date
)
SELECT
    E.branch,
    E.closing_base_date,
    E.closing_base_value,
    E.bridge_value,
    E.period_net_value,
    E.closing_base_value + E.bridge_value + E.period_net_value AS estimated_total_value,
    (SELECT SUM(total_stock_value) FROM item_totals IT WHERE IT.branch = E.branch) AS estimated_item_totals_check
FROM estimated_roll E
ORDER BY E.branch;

-- (2) Fechamento oficial: MAX(B9_DATA) <= end_date
WITH closure_le AS (
    SELECT B9_FILIAL AS branch, MAX(B9_DATA) AS closure_date
    FROM SB9010 WITH (NOLOCK)
    WHERE D_E_L_E_T_ = ''
      AND B9_DATA <> ''
      AND B9_DATA <= @end_date
      AND B9_FILIAL IN ('01', '02')
    GROUP BY B9_FILIAL
)
SELECT
    C.branch,
    C.closure_date,
    SUM(B9.B9_VINI1) AS official_closure_value,
    COUNT(DISTINCT RTRIM(B9.B9_LOCAL)) AS locations,
    COUNT(DISTINCT RTRIM(B9.B9_COD)) AS products
FROM closure_le C
INNER JOIN SB9010 B9 WITH (NOLOCK)
    ON B9.B9_FILIAL = C.branch
   AND B9.B9_DATA = C.closure_date
   AND B9.D_E_L_E_T_ = ''
GROUP BY C.branch, C.closure_date
ORDER BY C.branch;

-- (3) Fechamento exato na data do inventário (end_date)
SELECT
    B9.B9_FILIAL AS branch,
    B9.B9_DATA AS closure_date,
    SUM(B9.B9_VINI1) AS official_closure_value,
    COUNT(DISTINCT RTRIM(B9.B9_LOCAL)) AS locations,
    COUNT(DISTINCT RTRIM(B9.B9_COD)) AS products
FROM SB9010 B9 WITH (NOLOCK)
WHERE B9.D_E_L_E_T_ = ''
  AND B9.B9_DATA = @end_date
  AND B9.B9_FILIAL IN ('01', '02')
GROUP BY B9.B9_FILIAL, B9.B9_DATA
ORDER BY B9.B9_FILIAL;

-- (4) Saldo corrente SB2
SELECT
    B2.B2_FILIAL AS branch,
    SUM(B2.B2_VATU1) AS sb2_total_value,
    SUM(B2.B2_QATU) AS sb2_total_quantity,
    COUNT(DISTINCT RTRIM(B2.B2_LOCAL)) AS locations,
    COUNT(DISTINCT RTRIM(B2.B2_COD)) AS products
FROM SB2010 B2 WITH (NOLOCK)
WHERE B2.D_E_L_E_T_ = ''
  AND B2.B2_FILIAL IN ('01', '02')
GROUP BY B2.B2_FILIAL
ORDER BY B2.B2_FILIAL;

-- (5) Últimas 8 datas SB9 por filial (auditoria)
WITH ranked AS (
    SELECT
        B9_FILIAL AS branch,
        B9_DATA AS closure_date,
        SUM(B9_VINI1) AS closure_value,
        ROW_NUMBER() OVER (PARTITION BY B9_FILIAL ORDER BY B9_DATA DESC) AS rn
    FROM SB9010 WITH (NOLOCK)
    WHERE D_E_L_E_T_ = ''
      AND B9_DATA <> ''
      AND B9_FILIAL IN ('01', '02')
    GROUP BY B9_FILIAL, B9_DATA
)
SELECT branch, closure_date, closure_value
FROM ranked
WHERE rn <= 8
ORDER BY branch, closure_date DESC;
