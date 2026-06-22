-- Mapeamento sistemático: controle interno maio/2026 → OVs Protheus
-- Critérios: (1) produto ADJ ref da planilha (2) cliente+data abertura ±7d (3) homolog no mês

WITH Control AS (
    SELECT * FROM (VALUES
        ('070 26', 'flextronic',     '20260504', NULL,       'Lançamento'),
        ('071 26', '3RHO',           '20260504', NULL,       'Lançamento'),
        ('072 26', 'WEG Linhares',   '20260506', '19381065', 'Lançamento'),
        ('073 26', 'Wanke',          '20260508', NULL,       'Modificação'),
        ('074 26', 'Weg Motores',    '20260508', NULL,       'Modificação'),
        ('075 26', 'WEG Linhares',   '20260512', '90264221', 'Modificação'),
        ('076 26', 'WEG Linhares',   '20260513', '19373355', 'Lançamento'),
        ('077 26', 'WEG Linhares',   '20260514', '90263991', 'Modificação'),
        ('078 26', 'Buhler',         '20260514', NULL,       'Lançamento'),
        ('079 26', 'WEG Linhares',   '20260515', '90264229', 'Modificação'),
        ('080 26', 'WEG Linhares',   '20260519', NULL,       'Lançamento'),
        ('081 26', 'WEG Linhares',   '20260520', NULL,       'Lançamento'),
        ('082 26', 'WEG Linhares',   '20260522', NULL,       'Lançamento'),
        ('083 26', 'WEG Energia',    '20260525', NULL,       'Lançamento'),
        ('084 26', 'WEG Energia',    '20260525', NULL,       'Lançamento'),
        ('085 26', 'WEG Energia',    '20260525', NULL,       'Lançamento'),
        ('086 26', 'WEG Linhares',   '20260525', NULL,       'Lançamento')
    ) AS C(folder_code, client, control_open, product_ref, lmp_type)
),
Ad1Active AS (
    SELECT AD1.AD1_FILIAL, AD1.AD1_NROPOR, AD1.AD1_DESCRI
    FROM AD1010 AD1
    WHERE AD1.D_E_L_E_T_ = ''
),
AdjProducts AS (
    SELECT DISTINCT
        RTRIM(ADJ.ADJ_NROPOR) AS sale_number,
        RTRIM(ADJ.ADJ_FILIAL) AS branch,
        RTRIM(ADJ.ADJ_PROD) AS product_code
    FROM ADJ010 ADJ
    WHERE ADJ.D_E_L_E_T_ = ''
),
HomologMay AS (
    SELECT DISTINCT
        RTRIM(A.AIJ_NROPOR) AS sale_number,
        RTRIM(A.AIJ_FILIAL) AS branch,
        MIN(A.AIJ_DTINIC) AS first_homolog_may
    FROM AIJ010 A
    WHERE A.D_E_L_E_T_ = ''
      AND (
            (A.AIJ_PROVEN = '000002' AND A.AIJ_STAGE = '000012')
         OR (A.AIJ_PROVEN = '000003' AND A.AIJ_STAGE = '000012')
      )
      AND A.AIJ_DTINIC BETWEEN '20260501' AND '20260531'
    GROUP BY A.AIJ_NROPOR, A.AIJ_FILIAL
),
ByProductRef AS (
    SELECT
        C.folder_code,
        C.client,
        C.control_open,
        C.product_ref,
        AP.sale_number,
        AP.branch,
        AD1.AD1_DESCRI AS sale_description,
        HM.first_homolog_may,
        'product_ref' AS match_source
    FROM Control C
    INNER JOIN AdjProducts AP
        ON C.product_ref IS NOT NULL
       AND AP.product_code LIKE C.product_ref + '%'
    INNER JOIN Ad1Active AD1
        ON AD1.AD1_FILIAL = AP.branch
       AND AD1.AD1_NROPOR = AP.sale_number
    LEFT JOIN HomologMay HM
        ON HM.sale_number = AP.sale_number
       AND HM.branch = AP.branch
),
WankeProducts AS (
    SELECT
        C.folder_code,
        C.client,
        C.control_open,
        AP.product_code AS product_ref,
        AP.sale_number,
        AP.branch,
        AD1.AD1_DESCRI AS sale_description,
        HM.first_homolog_may,
        'wanke_9048' AS match_source
    FROM Control C
    CROSS JOIN AdjProducts AP
    INNER JOIN Ad1Active AD1
        ON AD1.AD1_FILIAL = AP.branch
       AND AD1.AD1_NROPOR = AP.sale_number
    LEFT JOIN HomologMay HM
        ON HM.sale_number = AP.sale_number
       AND HM.branch = AP.branch
    WHERE C.folder_code = '073 26'
      AND (
            AP.product_code LIKE '90480113%'
         OR AP.product_code LIKE '90480114%'
         OR AP.product_code LIKE '90480115%'
         OR AP.product_code LIKE '90480094%'
      )
),
ByClientDate AS (
    SELECT
        C.folder_code,
        C.client,
        C.control_open,
        NULL AS product_ref,
        RTRIM(AD1.AD1_NROPOR) AS sale_number,
        RTRIM(AD1.AD1_FILIAL) AS branch,
        AD1.AD1_DESCRI AS sale_description,
        HM.first_homolog_may,
        'client_date' AS match_source
    FROM Control C
    INNER JOIN Ad1Active AD1
        ON (
            (C.client LIKE '%flex%' AND AD1.AD1_DESCRI LIKE '%FLEX%')
         OR (C.client LIKE '%3RHO%' AND AD1.AD1_DESCRI LIKE '%3RHO%')
         OR (C.client LIKE '%Weg Motores%' AND AD1.AD1_DESCRI LIKE '%WEG MOTOR%')
         OR (C.client LIKE '%WEG Energia%' AND AD1.AD1_DESCRI LIKE '%WEG ENERG%')
         OR (C.client LIKE '%Buhler%' AND AD1.AD1_DESCRI LIKE '%BUHLER%')
         OR (C.client LIKE '%Wanke%' AND AD1.AD1_DESCRI LIKE '%WANKE%')
         OR (C.client LIKE '%WEG Linhares%' AND AD1.AD1_DESCRI LIKE '%WEG LINHARE%')
        )
    LEFT JOIN HomologMay HM
        ON HM.sale_number = AD1.AD1_NROPOR
       AND HM.branch = AD1.AD1_FILIAL
    WHERE C.product_ref IS NULL
      AND C.folder_code <> '073 26'
      AND HM.first_homolog_may IS NOT NULL
),
AllMatches AS (
    SELECT * FROM ByProductRef
    UNION ALL
    SELECT * FROM WankeProducts
    UNION ALL
    SELECT * FROM ByClientDate
)
SELECT
    folder_code,
    client,
    control_open,
    product_ref,
    sale_number,
    branch,
    sale_description,
    first_homolog_may,
    match_source
FROM AllMatches
ORDER BY folder_code, match_source, sale_number;
