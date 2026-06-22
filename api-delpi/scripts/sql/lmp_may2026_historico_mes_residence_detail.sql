-- Detalhe: evento no mês + residence >= 30 + homologação LMP (aproxima dashboard/controle)
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
    FROM AD1010 AD1 WHERE AD1.D_E_L_E_T_ = ''
),
PeriodActivity AS (
    SELECT A.AIJ_FILIAL, A.AIJ_NROPOR,
        MIN(A.AIJ_DTINIC) AS activity_start,
        COUNT(*) AS events_in_period,
        COUNT(DISTINCT A.AIJ_REVISA) AS revisions_in_period
    FROM AIJ010 A
    INNER JOIN Ad1Active AD1 ON AD1.AD1_FILIAL = A.AIJ_FILIAL AND AD1.AD1_NROPOR = A.AIJ_NROPOR
    INNER JOIN StageListing S ON S.AIJ_PROVEN = A.AIJ_PROVEN AND S.AIJ_STAGE = A.AIJ_STAGE
    WHERE A.D_E_L_E_T_ = '' AND A.AIJ_DTINIC BETWEEN '20260501' AND '20260531'
    GROUP BY A.AIJ_FILIAL, A.AIJ_NROPOR
),
AnchorCurrentRev AS (
    SELECT A.AIJ_FILIAL, A.AIJ_NROPOR, A.AIJ_DTINIC AS anchor_start, A.AIJ_STAGE AS anchor_stage,
        ROW_NUMBER() OVER (PARTITION BY A.AIJ_FILIAL, A.AIJ_NROPOR ORDER BY A.AIJ_DTINIC DESC, A.AIJ_HRINIC DESC, A.R_E_C_N_O_ DESC) AS rn
    FROM AIJ010 A
    INNER JOIN Ad1Active AD1 ON AD1.AD1_FILIAL = A.AIJ_FILIAL AND AD1.AD1_NROPOR = A.AIJ_NROPOR AND AD1.AD1_REVISA = A.AIJ_REVISA
    INNER JOIN LmpAnchor L ON L.AIJ_PROVEN = A.AIJ_PROVEN AND L.AIJ_STAGE = A.AIJ_STAGE
    WHERE A.D_E_L_E_T_ = ''
),
AnchorChosen AS (SELECT * FROM AnchorCurrentRev WHERE rn = 1),
EngMinutesClosed AS (
    SELECT A.AIJ_FILIAL, A.AIJ_NROPOR,
        SUM(CASE WHEN ISNULL(A.AIJ_DTINIC,'')<>'' AND ISNULL(A.AIJ_HRINIC,'')<>'' AND ISNULL(A.AIJ_DTENCE,'')<>'' AND ISNULL(A.AIJ_HRENCE,'')<>''
            THEN DATEDIFF(MINUTE,
                CAST(CONCAT(SUBSTRING(A.AIJ_DTINIC,1,4),'-',SUBSTRING(A.AIJ_DTINIC,5,2),'-',SUBSTRING(A.AIJ_DTINIC,7,2),' ',A.AIJ_HRINIC,':00') AS DATETIME),
                CAST(CONCAT(SUBSTRING(A.AIJ_DTENCE,1,4),'-',SUBSTRING(A.AIJ_DTENCE,5,2),'-',SUBSTRING(A.AIJ_DTENCE,7,2),' ',A.AIJ_HRENCE,':00') AS DATETIME))
            ELSE 0 END) AS eng_minutes_closed
    FROM AIJ010 A
    INNER JOIN Ad1Active AD1 ON AD1.AD1_FILIAL = A.AIJ_FILIAL AND AD1.AD1_NROPOR = A.AIJ_NROPOR
    INNER JOIN EngSupport E ON E.AIJ_PROVEN = A.AIJ_PROVEN AND E.AIJ_STAGE = A.AIJ_STAGE
    WHERE A.D_E_L_E_T_ = ''
    GROUP BY A.AIJ_FILIAL, A.AIJ_NROPOR
),
HasLmpFinalized AS (
    SELECT DISTINCT A.AIJ_FILIAL, A.AIJ_NROPOR
    FROM AIJ010 A
    INNER JOIN Ad1Active AD1 ON AD1.AD1_FILIAL = A.AIJ_FILIAL AND AD1.AD1_NROPOR = A.AIJ_NROPOR
    WHERE A.D_E_L_E_T_ = ''
      AND ((A.AIJ_PROVEN='000002' AND A.AIJ_STAGE='000012') OR (A.AIJ_PROVEN='000003' AND A.AIJ_STAGE='000012'))
),
Dashboard23 AS (
    SELECT * FROM (VALUES
        ('000054'),('000061'),('000084'),('000087'),('000088'),('000089'),('000090'),('000095'),('000097'),('000102'),
        ('000111'),('000120'),('002871'),('003403'),('003551'),('003561'),('003562'),('003568'),('003571'),
        ('003572'),('003573'),('003574'),('003578')
    ) AS D(sale_number)
)
SELECT
    C.sale_number,
    C.branch,
    C.sale_description,
    C.activity_start,
    C.anchor_start,
    C.anchor_stage,
    C.eng_minutes_closed,
    C.events_in_period,
    C.revisions_in_period,
    CASE WHEN D.sale_number IS NOT NULL THEN 1 ELSE 0 END AS no_dashboard_23,
    CASE WHEN C.eng_minutes_closed >= 30 AND LF.AIJ_NROPOR IS NOT NULL THEN 1 ELSE 0 END AS filtro_alvo
FROM (
    SELECT
        AD1.AD1_NROPOR AS sale_number,
        RTRIM(AD1.AD1_FILIAL) AS branch,
        RTRIM(AD1.AD1_DESCRI) AS sale_description,
        PA.activity_start,
        AC.anchor_start,
        AC.anchor_stage,
        ISNULL(EM.eng_minutes_closed, 0) AS eng_minutes_closed,
        PA.events_in_period,
        PA.revisions_in_period,
        AD1.AD1_FILIAL,
        AD1.AD1_NROPOR
    FROM Ad1Active AD1
    INNER JOIN PeriodActivity PA ON PA.AIJ_FILIAL = AD1.AD1_FILIAL AND PA.AIJ_NROPOR = AD1.AD1_NROPOR
    INNER JOIN AnchorChosen AC ON AC.AIJ_FILIAL = AD1.AD1_FILIAL AND AC.AIJ_NROPOR = AD1.AD1_NROPOR
    LEFT JOIN EngMinutesClosed EM ON EM.AIJ_FILIAL = AD1.AD1_FILIAL AND EM.AIJ_NROPOR = AD1.AD1_NROPOR
) C
LEFT JOIN HasLmpFinalized LF ON LF.AIJ_FILIAL = C.AD1_FILIAL AND LF.AIJ_NROPOR = C.AD1_NROPOR
LEFT JOIN Dashboard23 D ON D.sale_number = C.sale_number
WHERE ISNULL(C.eng_minutes_closed, 0) >= 30
  AND LF.AIJ_NROPOR IS NOT NULL
ORDER BY C.activity_start, C.sale_number;
