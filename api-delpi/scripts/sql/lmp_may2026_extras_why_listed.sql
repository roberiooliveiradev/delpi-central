-- Por que o filtro alvo lista OVs extras (sem pasta no controle maio/2026)?
-- OVs: 000087, 003331, 000102, 000061 (+ 003561/002871 dashboard mas residence baixo na simulação)
WITH TargetOvs AS (
    SELECT * FROM (VALUES
        ('000087', 'EXTRA_FILTRO_SEM_PASTA'),
        ('003331', 'EXTRA_FILTRO_SEM_PASTA'),
        ('000102', 'EXTRA_FILTRO_SEM_PASTA'),
        ('000061', 'EXTRA_FILTRO_SEM_PASTA'),
        ('003561', 'DASHBOARD_RESIDENCE_REAL'),
        ('002871', 'DASHBOARD_RESIDENCE_REAL')
    ) AS T(sale_number, motivo_grupo)
),
Ad1Active AS (
    SELECT AD1.AD1_FILIAL, AD1.AD1_NROPOR, AD1.AD1_REVISA, RTRIM(AD1.AD1_DESCRI) AS sale_description
    FROM AD1010 AD1 WHERE AD1.D_E_L_E_T_ = ''
),
-- Eventos listing em maio/2026 (qualquer revisão)
ListingMay AS (
    SELECT
        A.AIJ_FILIAL,
        A.AIJ_NROPOR,
        MIN(A.AIJ_DTINIC) AS first_listing_may,
        COUNT(*) AS listing_events_may,
        COUNT(DISTINCT A.AIJ_REVISA) AS revisions_with_listing_may,
        STRING_AGG(
            CONCAT(RTRIM(A.AIJ_PROVEN), '/', RTRIM(A.AIJ_STAGE), '@', A.AIJ_REVISA, ':', A.AIJ_DTINIC),
            ' | '
        ) WITHIN GROUP (ORDER BY A.AIJ_DTINIC, A.AIJ_HRINIC) AS listing_trace_may
    FROM AIJ010 A
    INNER JOIN Ad1Active AD1 ON AD1.AD1_FILIAL = A.AIJ_FILIAL AND AD1.AD1_NROPOR = A.AIJ_NROPOR
    WHERE A.D_E_L_E_T_ = ''
      AND A.AIJ_DTINIC BETWEEN '20260501' AND '20260531'
      AND (
            (A.AIJ_PROVEN = '000002' AND A.AIJ_STAGE IN ('000003', '000008', '000012'))
         OR (A.AIJ_PROVEN = '000003' AND A.AIJ_STAGE IN ('000003', '000012', '000002', '000008'))
      )
    GROUP BY A.AIJ_FILIAL, A.AIJ_NROPOR
),
-- Homologação LMP (000012) em qualquer revisão
HasHomolog AS (
    SELECT DISTINCT A.AIJ_FILIAL, A.AIJ_NROPOR,
        MIN(A.AIJ_DTINIC) AS first_homolog_date
    FROM AIJ010 A
    WHERE A.D_E_L_E_T_ = ''
      AND ((A.AIJ_PROVEN = '000002' AND A.AIJ_STAGE = '000012') OR (A.AIJ_PROVEN = '000003' AND A.AIJ_STAGE = '000012'))
    GROUP BY A.AIJ_FILIAL, A.AIJ_NROPOR
),
-- Amostra pura no mês (000008 / 000002|000008)
SampleMay AS (
    SELECT DISTINCT A.AIJ_FILIAL, A.AIJ_NROPOR
    FROM AIJ010 A
    WHERE A.D_E_L_E_T_ = ''
      AND A.AIJ_DTINIC BETWEEN '20260501' AND '20260531'
      AND (
            (A.AIJ_PROVEN = '000002' AND A.AIJ_STAGE = '000008')
         OR (A.AIJ_PROVEN = '000003' AND A.AIJ_STAGE IN ('000002', '000008'))
      )
),
-- Âncora LMP na revisão atual
LmpAnchor AS (
    SELECT * FROM (VALUES
        ('000002', '000003'), ('000002', '000012'),
        ('000003', '000003'), ('000003', '000012')
    ) AS L(AIJ_PROVEN, AIJ_STAGE)
),
AnchorCurrentRev AS (
    SELECT
        A.AIJ_FILIAL, A.AIJ_NROPOR,
        A.AIJ_DTINIC AS anchor_start,
        A.AIJ_STAGE AS anchor_stage,
        A.AIJ_PROVEN AS anchor_process,
        A.AIJ_REVISA AS anchor_revision,
        ROW_NUMBER() OVER (
            PARTITION BY A.AIJ_FILIAL, A.AIJ_NROPOR
            ORDER BY A.AIJ_DTINIC DESC, A.AIJ_HRINIC DESC, A.R_E_C_N_O_ DESC
        ) AS rn
    FROM AIJ010 A
    INNER JOIN Ad1Active AD1
        ON AD1.AD1_FILIAL = A.AIJ_FILIAL AND AD1.AD1_NROPOR = A.AIJ_NROPOR AND AD1.AD1_REVISA = A.AIJ_REVISA
    INNER JOIN LmpAnchor L ON L.AIJ_PROVEN = A.AIJ_PROVEN AND L.AIJ_STAGE = A.AIJ_STAGE
    WHERE A.D_E_L_E_T_ = ''
),
AnchorChosen AS (SELECT * FROM AnchorCurrentRev WHERE rn = 1),
EngSupport AS (
    SELECT * FROM (VALUES
        ('000002', '000003'), ('000002', '000008'), ('000002', '000012'),
        ('000003', '000003'), ('000003', '000012')
    ) AS E(AIJ_PROVEN, AIJ_STAGE)
),
EngMinutesClosed AS (
    SELECT A.AIJ_FILIAL, A.AIJ_NROPOR,
        SUM(CASE WHEN ISNULL(A.AIJ_DTINIC,'')<>'' AND ISNULL(A.AIJ_HRINIC,'')<>'' AND ISNULL(A.AIJ_DTENCE,'')<>'' AND ISNULL(A.AIJ_HRENCE,'')<>''
            THEN DATEDIFF(MINUTE,
                CAST(CONCAT(SUBSTRING(A.AIJ_DTINIC,1,4),'-',SUBSTRING(A.AIJ_DTINIC,5,2),'-',SUBSTRING(A.AIJ_DTINIC,7,2),' ',A.AIJ_HRINIC,':00') AS DATETIME),
                CAST(CONCAT(SUBSTRING(A.AIJ_DTENCE,1,4),'-',SUBSTRING(A.AIJ_DTENCE,5,2),'-',SUBSTRING(A.AIJ_DTENCE,7,2),' ',A.AIJ_HRENCE,':00') AS DATETIME))
            ELSE 0 END) AS eng_minutes_closed,
        COUNT(CASE WHEN ISNULL(A.AIJ_DTENCE,'')='' OR ISNULL(A.AIJ_HRENCE,'')='' THEN 1 END) AS open_eng_events
    FROM AIJ010 A
    INNER JOIN EngSupport E ON E.AIJ_PROVEN = A.AIJ_PROVEN AND E.AIJ_STAGE = A.AIJ_STAGE
    WHERE A.D_E_L_E_T_ = ''
    GROUP BY A.AIJ_FILIAL, A.AIJ_NROPOR
)
SELECT
    T.sale_number,
    T.motivo_grupo,
    AD1.sale_description,
    RTRIM(AD1.AD1_FILIAL) AS branch,
    AD1.AD1_REVISA AS current_revision,
    LM.first_listing_may,
    LM.listing_events_may,
    LM.revisions_with_listing_may,
    HH.first_homolog_date,
    CASE WHEN HH.AIJ_NROPOR IS NOT NULL THEN 1 ELSE 0 END AS has_homolog_lmp,
    CASE WHEN SM.AIJ_NROPOR IS NOT NULL THEN 1 ELSE 0 END AS sample_in_may,
    AC.anchor_start,
    AC.anchor_stage,
    AC.anchor_process,
    AC.anchor_revision,
    ISNULL(EM.eng_minutes_closed, 0) AS eng_minutes_closed,
    ISNULL(EM.open_eng_events, 0) AS open_eng_events,
    CASE WHEN LM.AIJ_NROPOR IS NOT NULL THEN 1 ELSE 0 END AS pass_evento_mes,
    CASE WHEN ISNULL(EM.eng_minutes_closed, 0) >= 30 THEN 1 ELSE 0 END AS pass_residence_sim,
    CASE
        WHEN LM.AIJ_NROPOR IS NULL THEN 'FALHA: sem evento listing em maio'
        WHEN HH.AIJ_NROPOR IS NULL THEN 'FALHA: sem homolog 000012'
        WHEN ISNULL(EM.eng_minutes_closed, 0) < 30 THEN 'FALHA: residence sim < 30 min'
        WHEN SM.AIJ_NROPOR IS NOT NULL AND HH.AIJ_NROPOR IS NULL THEN 'seria AMOSTRA, nao LMP'
        ELSE 'PASSA filtro alvo SQL'
    END AS diagnostico_filtro,
    LEFT(LM.listing_trace_may, 400) AS listing_trace_may
FROM TargetOvs T
INNER JOIN Ad1Active AD1 ON AD1.AD1_NROPOR = T.sale_number
LEFT JOIN ListingMay LM ON LM.AIJ_FILIAL = AD1.AD1_FILIAL AND LM.AIJ_NROPOR = AD1.AD1_NROPOR
LEFT JOIN HasHomolog HH ON HH.AIJ_FILIAL = AD1.AD1_FILIAL AND HH.AIJ_NROPOR = AD1.AD1_NROPOR
LEFT JOIN SampleMay SM ON SM.AIJ_FILIAL = AD1.AD1_FILIAL AND SM.AIJ_NROPOR = AD1.AD1_NROPOR
LEFT JOIN AnchorChosen AC ON AC.AIJ_FILIAL = AD1.AD1_FILIAL AND AC.AIJ_NROPOR = AD1.AD1_NROPOR
LEFT JOIN EngMinutesClosed EM ON EM.AIJ_FILIAL = AD1.AD1_FILIAL AND EM.AIJ_NROPOR = AD1.AD1_NROPOR
ORDER BY T.motivo_grupo, LM.first_listing_may, T.sale_number;
