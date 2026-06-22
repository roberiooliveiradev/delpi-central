-- Totais por estratégia de filtro — maio/2026 LMP (aproximação SQL)
WITH
StageListing AS (
    SELECT * FROM (VALUES
        ('000002', '000003'), ('000002', '000008'), ('000002', '000012'),
        ('000003', '000003'), ('000003', '000012'), ('000003', '000002'), ('000003', '000008')
    ) AS S(AIJ_PROVEN, AIJ_STAGE)
),
Ad1Active AS (
    SELECT AD1.AD1_FILIAL, AD1.AD1_NROPOR, AD1.AD1_REVISA
    FROM AD1010 AD1
    WHERE AD1.D_E_L_E_T_ = ''
),
FirstEng AS (
    SELECT A.AIJ_FILIAL, A.AIJ_NROPOR, MIN(A.AIJ_DTINIC) AS first_eng_date
    FROM AIJ010 A
    INNER JOIN Ad1Active AD1 ON AD1.AD1_FILIAL = A.AIJ_FILIAL AND AD1.AD1_NROPOR = A.AIJ_NROPOR
    INNER JOIN StageListing S ON S.AIJ_PROVEN = A.AIJ_PROVEN AND S.AIJ_STAGE = A.AIJ_STAGE
    WHERE A.D_E_L_E_T_ = '' AND ISNULL(A.AIJ_DTINIC, '') <> ''
    GROUP BY A.AIJ_FILIAL, A.AIJ_NROPOR
),
PeriodActivity AS (
    SELECT A.AIJ_FILIAL, A.AIJ_NROPOR
    FROM AIJ010 A
    INNER JOIN Ad1Active AD1 ON AD1.AD1_FILIAL = A.AIJ_FILIAL AND AD1.AD1_NROPOR = A.AIJ_NROPOR
    INNER JOIN StageListing S ON S.AIJ_PROVEN = A.AIJ_PROVEN AND S.AIJ_STAGE = A.AIJ_STAGE
    WHERE A.D_E_L_E_T_ = ''
      AND A.AIJ_DTINIC BETWEEN '20260501' AND '20260531'
    GROUP BY A.AIJ_FILIAL, A.AIJ_NROPOR
),
AnchorCurrentRev AS (
    SELECT A.AIJ_FILIAL, A.AIJ_NROPOR, A.AIJ_DTINIC AS anchor_start,
        ROW_NUMBER() OVER (
            PARTITION BY A.AIJ_FILIAL, A.AIJ_NROPOR
            ORDER BY A.AIJ_DTINIC DESC, A.AIJ_HRINIC DESC, A.R_E_C_N_O_ DESC
        ) AS rn
    FROM AIJ010 A
    INNER JOIN Ad1Active AD1
        ON AD1.AD1_FILIAL = A.AIJ_FILIAL AND AD1.AD1_NROPOR = A.AIJ_NROPOR AND AD1.AD1_REVISA = A.AIJ_REVISA
    WHERE A.D_E_L_E_T_ = ''
      AND ((A.AIJ_PROVEN = '000002' AND A.AIJ_STAGE IN ('000003','000012'))
        OR (A.AIJ_PROVEN = '000003' AND A.AIJ_STAGE IN ('000003','000012')))
),
AnchorChosen AS (
    SELECT * FROM AnchorCurrentRev WHERE rn = 1
),
OvFlags AS (
    SELECT
        AD1.AD1_FILIAL,
        AD1.AD1_NROPOR,
        CASE WHEN AC.anchor_start BETWEEN '20260501' AND '20260531' THEN 1 ELSE 0 END AS f_anchor,
        CASE WHEN FE.first_eng_date BETWEEN '20260501' AND '20260531' THEN 1 ELSE 0 END AS f_first_eng,
        CASE WHEN PA.AIJ_NROPOR IS NOT NULL THEN 1 ELSE 0 END AS f_historico,
        CASE WHEN AC.anchor_start BETWEEN '20260501' AND '20260531' OR FE.first_eng_date BETWEEN '20260501' AND '20260531' THEN 1 ELSE 0 END AS f_atual,
        CASE WHEN AC.anchor_start BETWEEN '20260501' AND '20260531' OR PA.AIJ_NROPOR IS NOT NULL THEN 1 ELSE 0 END AS f_proposto
    FROM Ad1Active AD1
    INNER JOIN AnchorChosen AC ON AC.AIJ_FILIAL = AD1.AD1_FILIAL AND AC.AIJ_NROPOR = AD1.AD1_NROPOR
    LEFT JOIN FirstEng FE ON FE.AIJ_FILIAL = AD1.AD1_FILIAL AND FE.AIJ_NROPOR = AD1.AD1_NROPOR
    LEFT JOIN PeriodActivity PA ON PA.AIJ_FILIAL = AD1.AD1_FILIAL AND PA.AIJ_NROPOR = AD1.AD1_NROPOR
)
SELECT
    SUM(f_anchor) AS total_somente_anchor_mes,
    SUM(f_first_eng) AS total_somente_first_eng_mes,
    SUM(f_historico) AS total_com_evento_historico_mes,
    SUM(f_atual) AS total_filtro_atual_anchor_or_first_eng,
    SUM(f_proposto) AS total_filtro_proposto_anchor_or_historico,
    SUM(CASE WHEN f_atual = 1 AND f_proposto = 0 THEN 1 ELSE 0 END) AS sai_no_proposto,
    SUM(CASE WHEN f_atual = 0 AND f_proposto = 1 THEN 1 ELSE 0 END) AS entra_no_proposto,
    SUM(CASE WHEN f_atual = 1 AND f_anchor = 0 AND f_first_eng = 1 THEN 1 ELSE 0 END) AS atual_so_por_first_eng,
    SUM(CASE WHEN f_atual = 1 AND f_anchor = 0 AND f_historico = 1 THEN 1 ELSE 0 END) AS atual_fora_anchor_mas_historico_mes
FROM OvFlags;
