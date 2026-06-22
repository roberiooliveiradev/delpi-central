-- Para cada pasta do controle: OVs com homolog LMP em maio/2026 mais próxima da data abertura
WITH Control AS (
    SELECT * FROM (VALUES
        ('070 26', 'flextronic',     '20260504', NULL),
        ('071 26', '3RHO',           '20260504', NULL),
        ('072 26', 'WEG Linhares',   '20260506', '19381065'),
        ('073 26', 'Wanke',          '20260508', NULL),
        ('074 26', 'Weg Motores',    '20260508', NULL),
        ('075 26', 'WEG Linhares',   '20260512', '90264221'),
        ('076 26', 'WEG Linhares',   '20260513', '19373355'),
        ('077 26', 'WEG Linhares',   '20260514', '90263991'),
        ('078 26', 'Buhler',         '20260514', NULL),
        ('079 26', 'WEG Linhares',   '20260515', '90264229'),
        ('080 26', 'WEG Linhares',   '20260519', NULL),
        ('081 26', 'WEG Linhares',   '20260520', NULL),
        ('082 26', 'WEG Linhares',   '20260522', NULL),
        ('083 26', 'WEG Energia',    '20260525', NULL),
        ('084 26', 'WEG Energia',    '20260525', NULL),
        ('085 26', 'WEG Energia',    '20260525', NULL),
        ('086 26', 'WEG Linhares',   '20260525', NULL)
    ) AS C(folder_code, client, control_open, product_ref)
),
HomologMay AS (
    SELECT
        RTRIM(A.AIJ_NROPOR) AS sale_number,
        RTRIM(A.AIJ_FILIAL) AS branch,
        MIN(A.AIJ_DTINIC) AS homolog_date
    FROM AIJ010 A
    WHERE A.D_E_L_E_T_ = ''
      AND (
            (A.AIJ_PROVEN = '000002' AND A.AIJ_STAGE = '000012')
         OR (A.AIJ_PROVEN = '000003' AND A.AIJ_STAGE = '000012')
      )
      AND A.AIJ_DTINIC BETWEEN '20260501' AND '20260531'
    GROUP BY A.AIJ_NROPOR, A.AIJ_FILIAL
),
AdjHit AS (
    SELECT DISTINCT
        C.folder_code,
        RTRIM(ADJ.ADJ_NROPOR) AS sale_number,
        RTRIM(ADJ.ADJ_FILIAL) AS branch
    FROM Control C
    INNER JOIN ADJ010 ADJ
        ON C.product_ref IS NOT NULL
       AND ADJ.ADJ_PROD LIKE C.product_ref + '%'
       AND ADJ.D_E_L_E_T_ = ''
),
Candidates AS (
    SELECT
        C.folder_code,
        C.client,
        C.control_open,
        C.product_ref,
        HM.sale_number,
        HM.branch,
        RTRIM(AD1.AD1_DESCRI) AS sale_description,
        HM.homolog_date,
        ABS(DATEDIFF(DAY, CONVERT(DATE, C.control_open, 112), CONVERT(DATE, HM.homolog_date, 112))) AS days_from_open,
        CASE WHEN AH.sale_number IS NOT NULL THEN 1 ELSE 0 END AS has_product_ref
    FROM Control C
    CROSS JOIN HomologMay HM
    INNER JOIN AD1010 AD1
        ON AD1.AD1_FILIAL = HM.branch
       AND AD1.AD1_NROPOR = HM.sale_number
       AND AD1.D_E_L_E_T_ = ''
    LEFT JOIN AdjHit AH
        ON AH.folder_code = C.folder_code
       AND AH.sale_number = HM.sale_number
       AND AH.branch = HM.branch
    WHERE
        (C.product_ref IS NOT NULL AND AH.sale_number IS NOT NULL)
        OR (
            C.product_ref IS NULL
            AND (
                (C.client LIKE '%flex%' AND AD1.AD1_DESCRI LIKE '%FLEX%')
             OR (C.client LIKE '%3RHO%' AND AD1.AD1_DESCRI LIKE '%3RHO%')
             OR (C.client LIKE '%Weg Motores%' AND AD1.AD1_DESCRI LIKE '%WEG MOTOR%')
             OR (C.client LIKE '%WEG Energia%' AND AD1.AD1_DESCRI LIKE '%WEG ENERG%')
             OR (C.client LIKE '%Buhler%' AND AD1.AD1_DESCRI LIKE '%BUHLER%')
             OR (C.client LIKE '%Wanke%' AND AD1.AD1_DESCRI LIKE '%WANKE%')
             OR (C.client LIKE '%WEG Linhares%' AND AD1.AD1_DESCRI LIKE '%WEG LINHARE%')
            )
        )
),
Ranked AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY folder_code, sale_number, branch
            ORDER BY has_product_ref DESC, days_from_open ASC
        ) AS rn_ov,
        ROW_NUMBER() OVER (
            PARTITION BY folder_code
            ORDER BY has_product_ref DESC, days_from_open ASC, sale_number
        ) AS rn_folder
    FROM Candidates
)
SELECT
    folder_code,
    client,
    control_open,
    product_ref,
    sale_number,
    branch,
    sale_description,
    homolog_date,
    days_from_open,
    has_product_ref,
    rn_folder
FROM Ranked
WHERE rn_ov = 1
  AND (has_product_ref = 1 OR days_from_open <= 7 OR folder_code IN ('073 26', '083 26', '084 26', '085 26'))
ORDER BY folder_code, rn_folder;
