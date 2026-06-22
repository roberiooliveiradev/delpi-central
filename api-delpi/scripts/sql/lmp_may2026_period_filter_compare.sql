-- Comparação de filtros de período LMP — maio/2026
-- Executar via: POST /apps/api-delpi/data/sql

WITH
StageListing AS (
    SELECT * FROM (VALUES
        ('000002', '000003'),
        ('000002', '000008'),
        ('000002', '000012'),
        ('000003', '000003'),
        ('000003', '000012'),
        ('000003', '000002'),
        ('000003', '000008')
    ) AS S(AIJ_PROVEN, AIJ_STAGE)
),
Ad1Active AS (
    SELECT AD1.AD1_FILIAL, AD1.AD1_NROPOR, AD1.AD1_REVISA, AD1.AD1_DESCRI
    FROM AD1010 AD1
    WHERE AD1.D_E_L_E_T_ = ''
),
FirstEng AS (
    SELECT
        A.AIJ_FILIAL,
        A.AIJ_NROPOR,
        MIN(A.AIJ_DTINIC) AS first_eng_date
    FROM AIJ010 A
    INNER JOIN Ad1Active AD1
        ON AD1.AD1_FILIAL = A.AIJ_FILIAL
       AND AD1.AD1_NROPOR = A.AIJ_NROPOR
    INNER JOIN StageListing S
        ON S.AIJ_PROVEN = A.AIJ_PROVEN
       AND S.AIJ_STAGE = A.AIJ_STAGE
    WHERE A.D_E_L_E_T_ = ''
      AND ISNULL(A.AIJ_DTINIC, '') <> ''
    GROUP BY A.AIJ_FILIAL, A.AIJ_NROPOR
),
PeriodActivity AS (
    SELECT
        A.AIJ_FILIAL,
        A.AIJ_NROPOR,
        MIN(A.AIJ_DTINIC) AS activity_start,
        MAX(COALESCE(NULLIF(A.AIJ_DTENCE, ''), A.AIJ_DTINIC)) AS activity_end,
        COUNT(*) AS events_in_period,
        COUNT(DISTINCT A.AIJ_REVISA) AS revisions_in_period,
        COUNT(DISTINCT CONCAT(A.AIJ_PROVEN, ':', A.AIJ_STAGE)) AS distinct_stages
    FROM AIJ010 A
    INNER JOIN Ad1Active AD1
        ON AD1.AD1_FILIAL = A.AIJ_FILIAL
       AND AD1.AD1_NROPOR = A.AIJ_NROPOR
    INNER JOIN StageListing S
        ON S.AIJ_PROVEN = A.AIJ_PROVEN
       AND S.AIJ_STAGE = A.AIJ_STAGE
    WHERE A.D_E_L_E_T_ = ''
      AND A.AIJ_DTINIC BETWEEN '20260501' AND '20260531'
    GROUP BY A.AIJ_FILIAL, A.AIJ_NROPOR
),
AnchorCurrentRev AS (
    SELECT
        A.AIJ_FILIAL,
        A.AIJ_NROPOR,
        A.AIJ_REVISA,
        A.AIJ_DTINIC AS anchor_start,
        COALESCE(NULLIF(A.AIJ_DTENCE, ''), A.AIJ_DTINIC) AS anchor_end,
        A.AIJ_PROVEN,
        A.AIJ_STAGE,
        ROW_NUMBER() OVER (
            PARTITION BY A.AIJ_FILIAL, A.AIJ_NROPOR
            ORDER BY A.AIJ_DTINIC DESC, A.AIJ_HRINIC DESC, A.R_E_C_N_O_ DESC
        ) AS rn
    FROM AIJ010 A
    INNER JOIN Ad1Active AD1
        ON AD1.AD1_FILIAL = A.AIJ_FILIAL
       AND AD1.AD1_NROPOR = A.AIJ_NROPOR
       AND AD1.AD1_REVISA = A.AIJ_REVISA
    WHERE A.D_E_L_E_T_ = ''
      AND (
            (A.AIJ_PROVEN = '000002' AND A.AIJ_STAGE IN ('000003', '000012'))
         OR (A.AIJ_PROVEN = '000003' AND A.AIJ_STAGE IN ('000003', '000012'))
      )
),
AnchorChosen AS (
    SELECT * FROM AnchorCurrentRev WHERE rn = 1
),
OvFlags AS (
    SELECT
        AD1.AD1_FILIAL,
        AD1.AD1_NROPOR,
        AD1.AD1_DESCRI,
        AC.anchor_start,
        AC.anchor_end,
        FE.first_eng_date,
        PA.activity_start,
        PA.events_in_period,
        PA.revisions_in_period,
        CASE WHEN AC.anchor_start BETWEEN '20260501' AND '20260531' THEN 1 ELSE 0 END AS filtro_anchor_mes,
        CASE WHEN FE.first_eng_date BETWEEN '20260501' AND '20260531' THEN 1 ELSE 0 END AS filtro_first_eng_mes,
        CASE WHEN PA.AIJ_NROPOR IS NOT NULL THEN 1 ELSE 0 END AS filtro_historico_mes,
        CASE
            WHEN AC.anchor_start BETWEEN '20260501' AND '20260531' THEN 1
            WHEN FE.first_eng_date BETWEEN '20260501' AND '20260531' THEN 1
            ELSE 0
        END AS filtro_atual_dashboard,
        CASE
            WHEN AC.anchor_start BETWEEN '20260501' AND '20260531' THEN 1
            WHEN PA.AIJ_NROPOR IS NOT NULL THEN 1
            ELSE 0
        END AS filtro_proposto_historico
    FROM Ad1Active AD1
    LEFT JOIN AnchorChosen AC
        ON AC.AIJ_FILIAL = AD1.AD1_FILIAL
       AND AC.AIJ_NROPOR = AD1.AD1_NROPOR
    LEFT JOIN FirstEng FE
        ON FE.AIJ_FILIAL = AD1.AD1_FILIAL
       AND FE.AIJ_NROPOR = AD1.AD1_NROPOR
    LEFT JOIN PeriodActivity PA
        ON PA.AIJ_FILIAL = AD1.AD1_FILIAL
       AND PA.AIJ_NROPOR = AD1.AD1_NROPOR
    WHERE AC.AIJ_NROPOR IS NOT NULL
)
SELECT
    AD1_NROPOR AS sale_number,
    RTRIM(AD1_FILIAL) AS branch,
    RTRIM(AD1_DESCRI) AS sale_description,
    anchor_start,
    first_eng_date,
    activity_start,
    events_in_period,
    revisions_in_period,
    filtro_anchor_mes,
    filtro_first_eng_mes,
    filtro_historico_mes,
    filtro_atual_dashboard,
    filtro_proposto_historico,
    CASE
        WHEN filtro_atual_dashboard = 1 AND filtro_proposto_historico = 0 THEN 'sai_no_proposto'
        WHEN filtro_atual_dashboard = 0 AND filtro_proposto_historico = 1 THEN 'entra_no_proposto'
        WHEN filtro_atual_dashboard <> filtro_historico_mes AND filtro_first_eng_mes = 1 AND filtro_historico_mes = 1 THEN 'first_eng_vs_historico'
        ELSE 'ok'
    END AS diff_tag
FROM OvFlags
WHERE filtro_atual_dashboard = 1
   OR filtro_proposto_historico = 1
ORDER BY
    filtro_atual_dashboard DESC,
    COALESCE(activity_start, anchor_start, first_eng_date),
    AD1_NROPOR;
