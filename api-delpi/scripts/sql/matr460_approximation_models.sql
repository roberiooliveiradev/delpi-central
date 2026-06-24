/*
  Modelos de aproximacao MATR460 vs referencia prints maio/2026.
  Executar: POST /apps/api-delpi/data/sql
*/

-- M1 SB2 total
SELECT
    'M1_sb2_total' AS model,
    B2_FILIAL AS branch,
    SUM(B2_VATU1) AS em_estoque,
    CAST(NULL AS FLOAT) AS em_processo,
    SUM(B2_VATU1) AS total_geral
FROM SB2010 WITH (NOLOCK)
WHERE D_E_L_E_T_ = ''
  AND B2_FILIAL IN ('01', '02')
GROUP BY B2_FILIAL;

-- M2 SB2 split locais processo (99/50/98)
SELECT
    'M2_sb2_excl_proc' AS model,
    B2.B2_FILIAL AS branch,
    SUM(CASE WHEN RTRIM(B2.B2_LOCAL) NOT IN ('99', '50', '98') THEN B2.B2_VATU1 ELSE 0 END) AS em_estoque,
    SUM(CASE WHEN RTRIM(B2.B2_LOCAL) IN ('99', '50', '98') THEN B2.B2_VATU1 ELSE 0 END) AS em_processo,
    SUM(B2.B2_VATU1) AS total_geral
FROM SB2010 B2 WITH (NOLOCK)
WHERE B2.D_E_L_E_T_ = ''
  AND B2.B2_FILIAL IN ('01', '02')
GROUP BY B2.B2_FILIAL;

-- M3 SB9 fev/28 total
SELECT
    'M3_sb9_feb28_total' AS model,
    B9_FILIAL AS branch,
    SUM(B9_VINI1) AS em_estoque,
    CAST(NULL AS FLOAT) AS em_processo,
    SUM(B9_VINI1) AS total_geral
FROM SB9010 WITH (NOLOCK)
WHERE D_E_L_E_T_ = ''
  AND B9_DATA = '20260228'
  AND B9_FILIAL IN ('01', '02')
GROUP BY B9_FILIAL;

-- M4 SB9 fev/28 split locais processo
SELECT
    'M4_sb9_feb28_split' AS model,
    B9.B9_FILIAL AS branch,
    SUM(CASE WHEN RTRIM(B9.B9_LOCAL) NOT IN ('99', '50', '98') THEN B9.B9_VINI1 ELSE 0 END) AS em_estoque,
    SUM(CASE WHEN RTRIM(B9.B9_LOCAL) IN ('99', '50', '98') THEN B9.B9_VINI1 ELSE 0 END) AS em_processo,
    SUM(B9.B9_VINI1) AS total_geral
FROM SB9010 B9 WITH (NOLOCK)
WHERE B9.D_E_L_E_T_ = ''
  AND B9.B9_DATA = '20260228'
  AND B9.B9_FILIAL IN ('01', '02')
GROUP BY B9.B9_FILIAL;

-- M5 SD4 saldo empenhado (D4_SLDEMP * B2_CM1)
SELECT
    'M5_sd4_empenho_saldo' AS model,
    D4.D4_FILIAL AS branch,
    CAST(NULL AS FLOAT) AS em_estoque,
    SUM(D4.D4_SLDEMP * COALESCE(NULLIF(B2.B2_CM1, 0), 0)) AS em_processo,
    SUM(D4.D4_SLDEMP * COALESCE(NULLIF(B2.B2_CM1, 0), 0)) AS total_geral
FROM SD4010 D4 WITH (NOLOCK)
INNER JOIN SB2010 B2 WITH (NOLOCK)
    ON B2.B2_FILIAL = D4.D4_FILIAL
   AND B2.B2_COD = D4.D4_COD
   AND RTRIM(B2.B2_LOCAL) = RTRIM(D4.D4_LOCAL)
   AND B2.D_E_L_E_T_ = ''
WHERE D4.D_E_L_E_T_ = ''
  AND D4.D4_FILIAL IN ('01', '02')
  AND D4.D4_SLDEMP > 0
GROUP BY D4.D4_FILIAL;

-- M6 SB2 excl proc + SD4 empenho (hibrido estilo P7)
SELECT
    'M6_sb2_excl_plus_sd4' AS model,
    x.branch,
    x.em_estoque,
    COALESCE(e.em_processo, 0) AS em_processo,
    x.em_estoque + COALESCE(e.em_processo, 0) AS total_geral
FROM (
    SELECT
        B2.B2_FILIAL AS branch,
        SUM(CASE WHEN RTRIM(B2.B2_LOCAL) NOT IN ('99', '50', '98') THEN B2.B2_VATU1 ELSE 0 END) AS em_estoque
    FROM SB2010 B2 WITH (NOLOCK)
    WHERE B2.D_E_L_E_T_ = ''
      AND B2.B2_FILIAL IN ('01', '02')
    GROUP BY B2.B2_FILIAL
) x
LEFT JOIN (
    SELECT
        D4.D4_FILIAL AS branch,
        SUM(D4.D4_SLDEMP * COALESCE(NULLIF(B2.B2_CM1, 0), 0)) AS em_processo
    FROM SD4010 D4 WITH (NOLOCK)
    INNER JOIN SB2010 B2 WITH (NOLOCK)
        ON B2.B2_FILIAL = D4.D4_FILIAL
       AND B2.B2_COD = D4.D4_COD
       AND RTRIM(B2.B2_LOCAL) = RTRIM(D4.D4_LOCAL)
       AND B2.D_E_L_E_T_ = ''
    WHERE D4.D_E_L_E_T_ = ''
      AND D4.D4_FILIAL IN ('01', '02')
      AND D4.D4_SLDEMP > 0
    GROUP BY D4.D4_FILIAL
) e ON e.branch = x.branch;

-- M7 SD4 D4_EMPROC * B2_CM1
SELECT
    'M7_sd4_emproc' AS model,
    D4.D4_FILIAL AS branch,
    CAST(NULL AS FLOAT) AS em_estoque,
    SUM(D4.D4_EMPROC * COALESCE(NULLIF(B2.B2_CM1, 0), 0)) AS em_processo,
    SUM(D4.D4_EMPROC * COALESCE(NULLIF(B2.B2_CM1, 0), 0)) AS total_geral
FROM SD4010 D4 WITH (NOLOCK)
INNER JOIN SB2010 B2 WITH (NOLOCK)
    ON B2.B2_FILIAL = D4.D4_FILIAL
   AND B2.B2_COD = D4.D4_COD
   AND RTRIM(B2.B2_LOCAL) = RTRIM(D4.D4_LOCAL)
   AND B2.D_E_L_E_T_ = ''
WHERE D4.D_E_L_E_T_ = ''
  AND D4.D4_FILIAL IN ('01', '02')
  AND D4.D4_EMPROC > 0
GROUP BY D4.D4_FILIAL;

-- M8 SB2: armazem 01 = EE, loc 99 = EP
SELECT
    'M8_sb2_loc01_plus_99' AS model,
    B2.B2_FILIAL AS branch,
    SUM(CASE WHEN RTRIM(B2.B2_LOCAL) = '01' THEN B2.B2_VATU1 ELSE 0 END) AS em_estoque,
    SUM(CASE WHEN RTRIM(B2.B2_LOCAL) = '99' THEN B2.B2_VATU1 ELSE 0 END) AS em_processo,
    SUM(CASE WHEN RTRIM(B2.B2_LOCAL) IN ('01', '99') THEN B2.B2_VATU1 ELSE 0 END) AS total_geral
FROM SB2010 B2 WITH (NOLOCK)
WHERE B2.D_E_L_E_T_ = ''
  AND B2.B2_FILIAL IN ('01', '02')
GROUP BY B2.B2_FILIAL;

-- M9 SB2 total + SD4 empenho como EP (EE=SB2 all)
SELECT
    'M9_sb2_all_plus_sd4' AS model,
    s.branch,
    s.em_estoque,
    COALESCE(e.em_processo, 0) AS em_processo,
    s.em_estoque + COALESCE(e.em_processo, 0) AS total_geral
FROM (
    SELECT B2_FILIAL AS branch, SUM(B2_VATU1) AS em_estoque
    FROM SB2010 WITH (NOLOCK)
    WHERE D_E_L_E_T_ = '' AND B2_FILIAL IN ('01', '02')
    GROUP BY B2_FILIAL
) s
LEFT JOIN (
    SELECT
        D4.D4_FILIAL AS branch,
        SUM(D4.D4_SLDEMP * COALESCE(NULLIF(B2.B2_CM1, 0), 0)) AS em_processo
    FROM SD4010 D4 WITH (NOLOCK)
    INNER JOIN SB2010 B2 WITH (NOLOCK)
        ON B2.B2_FILIAL = D4.D4_FILIAL
       AND B2.B2_COD = D4.D4_COD
       AND RTRIM(B2.B2_LOCAL) = RTRIM(D4.D4_LOCAL)
       AND B2.D_E_L_E_T_ = ''
    WHERE D4.D_E_L_E_T_ = ''
      AND D4.D4_FILIAL IN ('01', '02')
      AND D4.D4_SLDEMP > 0
    GROUP BY D4.D4_FILIAL
) e ON e.branch = s.branch;
