-- Filtro: SOMENTE evento listing no mês + residence >= 30 min (simulado)
-- Objetivo: aproximar contagem do controle interno (17) vs dashboard (23)
-- Executar: POST /apps/api-delpi/data/sql

WITH
StageListing AS (
    SELECT * FROM (VALUES
        ('000002', '000003'), ('000002', '000008'), ('000002', '000012'),
        ('000003', '000003'), ('000003', '000012'), ('000003', '000002'), ('000003', '000008')
    ) AS S(AIJ_PROVEN, AIJ_STAGE)
),
EngSupport AS (
    SELECT * FROM (VALUES
        ('000002', '000003'), ('000002', '000008'), ('000002', '000012'),
        ('000003', '000003'), ('000003', '000012')
    ) AS E(AIJ_PROVEN, AIJ_STAGE)
),
LmpAnchor AS (
    SELECT * FROM (VALUES
        ('000002', '000003'), ('000002', '000012'),
        ('000003', '000003'), ('000003', '000012')
    ) AS L(AIJ_PROVEN, AIJ_STAGE)
),
Ad1Active AS (
    SELECT AD1.AD1_FILIAL, AD1.AD1_NROPOR, AD1.AD1_REVISA, AD1.AD1_DESCRI
    FROM AD1010 AD1
    WHERE AD1.D_E_L_E_T_ = ''
),
-- Obrigatório: ao menos 1 evento listing no mês (qualquer revisão)
PeriodActivity AS (
    SELECT
        A.AIJ_FILIAL,
        A.AIJ_NROPOR,
        MIN(A.AIJ_DTINIC) AS activity_start,
        MAX(COALESCE(NULLIF(A.AIJ_DTENCE, ''), A.AIJ_DTINIC)) AS activity_end,
        COUNT(*) AS events_in_period,
        COUNT(DISTINCT A.AIJ_REVISA) AS revisions_in_period
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
-- Âncora LMP na revisão atual do AD1010
AnchorCurrentRev AS (
    SELECT
        A.AIJ_FILIAL,
        A.AIJ_NROPOR,
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
    INNER JOIN LmpAnchor L
        ON L.AIJ_PROVEN = A.AIJ_PROVEN
       AND L.AIJ_STAGE = A.AIJ_STAGE
    WHERE A.D_E_L_E_T_ = ''
),
AnchorChosen AS (
    SELECT * FROM AnchorCurrentRev WHERE rn = 1
),
-- Minutos engenharia (apoio eng.) — eventos encerrados, todas as revisões
EngMinutesClosed AS (
    SELECT
        A.AIJ_FILIAL,
        A.AIJ_NROPOR,
        SUM(
            CASE
                WHEN ISNULL(A.AIJ_DTINIC, '') <> ''
                 AND ISNULL(A.AIJ_HRINIC, '') <> ''
                 AND ISNULL(A.AIJ_DTENCE, '') <> ''
                 AND ISNULL(A.AIJ_HRENCE, '') <> ''
                THEN DATEDIFF(
                    MINUTE,
                    CAST(
                        CONCAT(
                            SUBSTRING(A.AIJ_DTINIC, 1, 4), '-',
                            SUBSTRING(A.AIJ_DTINIC, 5, 2), '-',
                            SUBSTRING(A.AIJ_DTINIC, 7, 2), ' ',
                            A.AIJ_HRINIC, ':00'
                        ) AS DATETIME
                    ),
                    CAST(
                        CONCAT(
                            SUBSTRING(A.AIJ_DTENCE, 1, 4), '-',
                            SUBSTRING(A.AIJ_DTENCE, 5, 2), '-',
                            SUBSTRING(A.AIJ_DTENCE, 7, 2), ' ',
                            A.AIJ_HRENCE, ':00'
                        ) AS DATETIME
                    )
                )
                ELSE 0
            END
        ) AS eng_minutes_closed
    FROM AIJ010 A
    INNER JOIN Ad1Active AD1
        ON AD1.AD1_FILIAL = A.AIJ_FILIAL
       AND AD1.AD1_NROPOR = A.AIJ_NROPOR
    INNER JOIN EngSupport E
        ON E.AIJ_PROVEN = A.AIJ_PROVEN
       AND E.AIJ_STAGE = A.AIJ_STAGE
    WHERE A.D_E_L_E_T_ = ''
    GROUP BY A.AIJ_FILIAL, A.AIJ_NROPOR
),
-- Passou por homologação LMP (000012) em qualquer revisão
HasLmpFinalized AS (
    SELECT DISTINCT A.AIJ_FILIAL, A.AIJ_NROPOR
    FROM AIJ010 A
    INNER JOIN Ad1Active AD1
        ON AD1.AD1_FILIAL = A.AIJ_FILIAL
       AND AD1.AD1_NROPOR = A.AIJ_NROPOR
    WHERE A.D_E_L_E_T_ = ''
      AND (
            (A.AIJ_PROVEN = '000002' AND A.AIJ_STAGE = '000012')
         OR (A.AIJ_PROVEN = '000003' AND A.AIJ_STAGE = '000012')
      )
),
-- Amostra no mês sem homologação
SampleInPeriod AS (
    SELECT DISTINCT A.AIJ_FILIAL, A.AIJ_NROPOR
    FROM AIJ010 A
    INNER JOIN Ad1Active AD1
        ON AD1.AD1_FILIAL = A.AIJ_FILIAL
       AND AD1.AD1_NROPOR = A.AIJ_NROPOR
    WHERE A.D_E_L_E_T_ = ''
      AND A.AIJ_DTINIC BETWEEN '20260501' AND '20260531'
      AND (
            (A.AIJ_PROVEN = '000002' AND A.AIJ_STAGE = '000008')
         OR (A.AIJ_PROVEN = '000003' AND A.AIJ_STAGE IN ('000002', '000008'))
      )
),
Candidates AS (
    SELECT
        AD1.AD1_NROPOR AS sale_number,
        RTRIM(AD1.AD1_FILIAL) AS branch,
        RTRIM(AD1.AD1_DESCRI) AS sale_description,
        PA.activity_start,
        PA.activity_end,
        PA.events_in_period,
        PA.revisions_in_period,
        AC.anchor_start,
        AC.anchor_end,
        AC.AIJ_STAGE AS anchor_stage,
        ISNULL(EM.eng_minutes_closed, 0) AS eng_minutes_closed,
        CASE WHEN LF.AIJ_NROPOR IS NOT NULL THEN 1 ELSE 0 END AS has_lmp_finalized,
        CASE WHEN SP.AIJ_NROPOR IS NOT NULL THEN 1 ELSE 0 END AS sample_in_period,
        CASE WHEN ISNULL(EM.eng_minutes_closed, 0) >= 30 THEN 1 ELSE 0 END AS pass_residence_30,
        CASE WHEN AC.anchor_start BETWEEN '20260501' AND '20260531' THEN 1 ELSE 0 END AS anchor_in_mes
    FROM Ad1Active AD1
    INNER JOIN PeriodActivity PA
        ON PA.AIJ_FILIAL = AD1.AD1_FILIAL
       AND PA.AIJ_NROPOR = AD1.AD1_NROPOR
    INNER JOIN AnchorChosen AC
        ON AC.AIJ_FILIAL = AD1.AD1_FILIAL
       AND AC.AIJ_NROPOR = AD1.AD1_NROPOR
    LEFT JOIN EngMinutesClosed EM
        ON EM.AIJ_FILIAL = AD1.AD1_FILIAL
       AND EM.AIJ_NROPOR = AD1.AD1_NROPOR
    LEFT JOIN HasLmpFinalized LF
        ON LF.AIJ_FILIAL = AD1.AD1_FILIAL
       AND LF.AIJ_NROPOR = AD1.AD1_NROPOR
    LEFT JOIN SampleInPeriod SP
        ON SP.AIJ_FILIAL = AD1.AD1_FILIAL
       AND SP.AIJ_NROPOR = AD1.AD1_NROPOR
)
SELECT
    COUNT(*) AS total_somente_evento_mes,
    SUM(pass_residence_30) AS com_residence_30,
    SUM(CASE WHEN pass_residence_30 = 1 AND has_lmp_finalized = 1 THEN 1 ELSE 0 END) AS residence30_e_homologada,
    SUM(CASE WHEN pass_residence_30 = 1 AND (has_lmp_finalized = 1 OR sample_in_period = 0) THEN 1 ELSE 0 END) AS residence30_sem_amostra_pura,
    SUM(CASE WHEN pass_residence_30 = 1 AND has_lmp_finalized = 1 AND anchor_in_mes = 1 THEN 1 ELSE 0 END) AS residence30_homolog_anchor_mes,
    SUM(CASE WHEN pass_residence_30 = 1 AND has_lmp_finalized = 1 AND sample_in_period = 0 THEN 1 ELSE 0 END) AS residence30_homolog_nao_amostra_mes
FROM Candidates;
