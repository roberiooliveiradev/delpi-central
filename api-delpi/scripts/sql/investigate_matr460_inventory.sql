/*
  Investigação MATR460 / Registro de Inventário vs. fontes SQL (jun/2026).

  Result sets (ordem):
    1) sb9_closure_dates_2026      — datas de fechamento SB9 por filial (2026)
    2) sb9_value_by_date           — soma B9_VINI1 por B9_DATA (2026, filiais 01/02)
    3) sb9_vs_sb2_vs_ref           — comparativo filial (SB9 fev/28, SB9 max<=mai, SB2, refs MATR460)
    4) sb9_by_local_feb28          — breakdown por local na última data SB9 antes de mai/2026
    5) sb2_by_local_current        — breakdown SB2 atual por local
    6) sd3_bridge_period_summary   — SD3 ponte+período (mar–mai/2026) por TM e filial
    7) sc2_open_orders_wip_proxy   — proxy WIP: SC2 saldo em aberto (C2_QUJE < C2_QUANT)
    8) inventory_related_objects    — views/tabelas com nome invent/estoque/MATR no banco
*/
SET NOCOUNT ON;

DECLARE @end_date CHAR(8) = '20260531';
DECLARE @start_date CHAR(8) = '20260501';
DECLARE @end_exclusive CHAR(8) = '20260601';
DECLARE @last_sb9_before_may CHAR(8) = '20260228';

-- (1) Datas SB9 em 2026
SELECT
    B9_FILIAL AS branch,
    B9_DATA AS closure_date,
    COUNT(*) AS record_count,
    SUM(B9_VINI1) AS closure_value,
    COUNT(DISTINCT RTRIM(B9_LOCAL)) AS location_count,
    COUNT(DISTINCT RTRIM(B9_COD)) AS product_count
FROM SB9010 WITH (NOLOCK)
WHERE D_E_L_E_T_ = ''
  AND B9_DATA >= '20260101'
  AND B9_DATA <= '20261231'
  AND B9_FILIAL IN ('01', '02')
GROUP BY B9_FILIAL, B9_DATA
ORDER BY B9_FILIAL, B9_DATA DESC;

-- (2) Soma por data (auditoria rápida)
SELECT
    B9_FILIAL AS branch,
    B9_DATA AS closure_date,
    SUM(B9_VINI1) AS total_value,
    SUM(B9_QINI) AS total_qty
FROM SB9010 WITH (NOLOCK)
WHERE D_E_L_E_T_ = ''
  AND B9_DATA >= '20260101'
  AND B9_FILIAL IN ('01', '02')
GROUP BY B9_FILIAL, B9_DATA
ORDER BY B9_FILIAL, B9_DATA;

-- (3) Comparativo consolidado por filial
WITH sb9_feb AS (
    SELECT B9_FILIAL AS branch, SUM(B9_VINI1) AS val
    FROM SB9010 WITH (NOLOCK)
    WHERE D_E_L_E_T_ = '' AND B9_DATA = @last_sb9_before_may AND B9_FILIAL IN ('01', '02')
    GROUP BY B9_FILIAL
),
sb9_on_end AS (
    SELECT B9_FILIAL AS branch, SUM(B9_VINI1) AS val
    FROM SB9010 WITH (NOLOCK)
    WHERE D_E_L_E_T_ = '' AND B9_DATA = @end_date AND B9_FILIAL IN ('01', '02')
    GROUP BY B9_FILIAL
),
sb9_max_le AS (
    SELECT B9.B9_FILIAL AS branch, SUM(B9.B9_VINI1) AS val
    FROM SB9010 B9 WITH (NOLOCK)
    INNER JOIN (
        SELECT B9_FILIAL, MAX(B9_DATA) AS md
        FROM SB9010 WITH (NOLOCK)
        WHERE D_E_L_E_T_ = '' AND B9_DATA <= @end_date AND B9_FILIAL IN ('01', '02')
        GROUP BY B9_FILIAL
    ) M ON M.B9_FILIAL = B9.B9_FILIAL AND M.md = B9.B9_DATA
    WHERE B9.D_E_L_E_T_ = ''
    GROUP BY B9.B9_FILIAL
),
sb2_now AS (
    SELECT B2_FILIAL AS branch, SUM(B2_VATU1) AS val
    FROM SB2010 WITH (NOLOCK)
    WHERE D_E_L_E_T_ = '' AND B2_FILIAL IN ('01', '02')
    GROUP BY B2_FILIAL
)
SELECT
    B.branch,
    F.val AS sb9_feb28_value,
    O.val AS sb9_on_end_date_value,
    M.val AS sb9_max_le_end_value,
    S.val AS sb2_current_value
FROM (SELECT '01' AS branch UNION ALL SELECT '02') B
LEFT JOIN sb9_feb F ON F.branch = B.branch
LEFT JOIN sb9_on_end O ON O.branch = B.branch
LEFT JOIN sb9_max_le M ON M.branch = B.branch
LEFT JOIN sb2_now S ON S.branch = B.branch
ORDER BY B.branch;

-- (4) SB9 por local (fev/28)
SELECT
    B9_FILIAL AS branch,
    RTRIM(B9_LOCAL) AS location,
    COUNT(*) AS records,
    SUM(B9_VINI1) AS total_value
FROM SB9010 WITH (NOLOCK)
WHERE D_E_L_E_T_ = ''
  AND B9_DATA = @last_sb9_before_may
  AND B9_FILIAL IN ('01', '02')
GROUP BY B9_FILIAL, RTRIM(B9_LOCAL)
ORDER BY B9_FILIAL, total_value DESC;

-- (5) SB2 atual por local
SELECT
    B2_FILIAL AS branch,
    RTRIM(B2_LOCAL) AS location,
    COUNT(*) AS records,
    SUM(B2_VATU1) AS total_value
FROM SB2010 WITH (NOLOCK)
WHERE D_E_L_E_T_ = ''
  AND B2_FILIAL IN ('01', '02')
GROUP BY B2_FILIAL, RTRIM(B2_LOCAL)
ORDER BY B2_FILIAL, total_value DESC;

-- (6) SD3 mar–mai/2026 — resumo por filial e tipo TM
SELECT
    D3.D3_FILIAL AS branch,
    CASE WHEN D3.D3_TM < '500' THEN 'entrada' ELSE 'saida' END AS movement_side,
    LEFT(RTRIM(D3.D3_TM), 3) AS tm_prefix,
    COUNT(*) AS movement_count,
    SUM(CASE WHEN D3.D3_TM < '500' THEN D3.D3_CUSTO1 ELSE -D3.D3_CUSTO1 END) AS net_value
FROM SD3010 D3 WITH (NOLOCK)
WHERE D3.D_E_L_E_T_ = ''
  AND D3.D3_FILIAL IN ('01', '02')
  AND D3.D3_EMISSAO >= '20260301'
  AND D3.D3_EMISSAO < @end_exclusive
GROUP BY
    D3.D3_FILIAL,
    CASE WHEN D3.D3_TM < '500' THEN 'entrada' ELSE 'saida' END,
    LEFT(RTRIM(D3.D3_TM), 3)
ORDER BY D3.D3_FILIAL, net_value;

-- (7) Proxy WIP — SC2 ordens com saldo em aberto (valor proporcional C2_VATU1)
SELECT
    C2.C2_FILIAL AS branch,
    COUNT(*) AS open_order_count,
    SUM(C2.C2_QUANT - C2.C2_QUJE) AS open_quantity,
    SUM(
        CASE
            WHEN C2.C2_QUANT > 0
            THEN C2.C2_VATU1 * ((C2.C2_QUANT - C2.C2_QUJE) / C2.C2_QUANT)
            ELSE 0
        END
    ) AS open_value_proxy
FROM SC2010 C2 WITH (NOLOCK)
WHERE C2.D_E_L_E_T_ = ''
  AND C2.C2_FILIAL IN ('01', '02')
  AND RTRIM(C2.C2_DATRF) = ''
  AND (C2.C2_QUANT - C2.C2_QUJE) > 0
GROUP BY C2.C2_FILIAL
ORDER BY C2.C2_FILIAL;

-- (8) Objetos SQL relacionados a inventário/estoque
SELECT TOP 40
    o.type_desc AS object_type,
    SCHEMA_NAME(o.schema_id) AS schema_name,
    o.name AS object_name
FROM sys.objects o
WHERE o.type IN ('V', 'U', 'IF', 'TF')
  AND (
    o.name LIKE '%INVENT%'
    OR o.name LIKE '%ESTOQ%'
    OR o.name LIKE '%MATR%'
    OR o.name LIKE '%SB9%'
    OR o.name LIKE '%REGINV%'
  )
ORDER BY o.type_desc, o.name;
