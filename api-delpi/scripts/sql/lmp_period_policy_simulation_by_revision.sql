-- Simulação unificada: políticas por REVISÃO + reclassificação strict OUTRO (<30 min)
-- row_kind: TOTAL | DETAIL_HOMOLOG_REV | ONLY_CURRENT_OV
DECLARE @date_start CHAR(8) = '20260501';
DECLARE @date_end   CHAR(8) = '20260531';

WITH
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
    SELECT AD1.AD1_FILIAL, AD1.AD1_NROPOR, AD1.AD1_REVISA, RTRIM(AD1.AD1_DESCRI) AS sale_description
    FROM AD1010 AD1 WHERE AD1.D_E_L_E_T_ = ''
),
RevHomolog AS (
    SELECT A.AIJ_FILIAL, A.AIJ_NROPOR, A.AIJ_REVISA AS revision, MIN(A.AIJ_DTINIC) AS homolog_date
    FROM AIJ010 A
    INNER JOIN Ad1Active AD1 ON AD1.AD1_FILIAL = A.AIJ_FILIAL AND AD1.AD1_NROPOR = A.AIJ_NROPOR
    WHERE A.D_E_L_E_T_ = ''
      AND ((A.AIJ_PROVEN = '000002' AND A.AIJ_STAGE = '000012') OR (A.AIJ_PROVEN = '000003' AND A.AIJ_STAGE = '000012'))
    GROUP BY A.AIJ_FILIAL, A.AIJ_NROPOR, A.AIJ_REVISA
),
RevEngMinutes AS (
    SELECT A.AIJ_FILIAL, A.AIJ_NROPOR, A.AIJ_REVISA AS revision,
        MIN(A.AIJ_DTINIC) AS rev_first_eng,
        SUM(CASE WHEN ISNULL(A.AIJ_DTINIC,'')<>'' AND ISNULL(A.AIJ_HRINIC,'')<>'' AND ISNULL(A.AIJ_DTENCE,'')<>'' AND ISNULL(A.AIJ_HRENCE,'')<>''
            THEN DATEDIFF(MINUTE,
                CAST(CONCAT(SUBSTRING(A.AIJ_DTINIC,1,4),'-',SUBSTRING(A.AIJ_DTINIC,5,2),'-',SUBSTRING(A.AIJ_DTINIC,7,2),' ',A.AIJ_HRINIC,':00') AS DATETIME),
                CAST(CONCAT(SUBSTRING(A.AIJ_DTENCE,1,4),'-',SUBSTRING(A.AIJ_DTENCE,5,2),'-',SUBSTRING(A.AIJ_DTENCE,7,2),' ',A.AIJ_HRENCE,':00') AS DATETIME))
            ELSE 0 END) AS eng_minutes_closed
    FROM AIJ010 A
    INNER JOIN EngSupport E ON E.AIJ_PROVEN = A.AIJ_PROVEN AND E.AIJ_STAGE = A.AIJ_STAGE
    WHERE A.D_E_L_E_T_ = '' GROUP BY A.AIJ_FILIAL, A.AIJ_NROPOR, A.AIJ_REVISA
),
RevSample AS (
    SELECT DISTINCT A.AIJ_FILIAL, A.AIJ_NROPOR, A.AIJ_REVISA AS revision
    FROM AIJ010 A
    WHERE A.D_E_L_E_T_ = ''
      AND ((A.AIJ_PROVEN='000002' AND A.AIJ_STAGE='000008') OR (A.AIJ_PROVEN='000003' AND A.AIJ_STAGE IN ('000002','000008')))
),
RevCycleRows AS (
    SELECT RH.AIJ_FILIAL, RH.AIJ_NROPOR, RH.revision, AD1.sale_description, AD1.AD1_REVISA AS current_revision,
        RH.homolog_date, ISNULL(REM.eng_minutes_closed,0) AS eng_minutes_closed, REM.rev_first_eng,
        CASE WHEN RS.revision IS NOT NULL THEN 1 ELSE 0 END AS has_sample_on_rev,
        CASE WHEN ISNULL(REM.eng_minutes_closed,0) >= 30 THEN 'LMP' ELSE 'OUTRO' END AS tipo_proposto_strict
    FROM RevHomolog RH
    INNER JOIN Ad1Active AD1 ON AD1.AD1_FILIAL = RH.AIJ_FILIAL AND AD1.AD1_NROPOR = RH.AIJ_NROPOR
    LEFT JOIN RevEngMinutes REM ON REM.AIJ_FILIAL=RH.AIJ_FILIAL AND REM.AIJ_NROPOR=RH.AIJ_NROPOR AND REM.revision=RH.revision
    LEFT JOIN RevSample RS ON RS.AIJ_FILIAL=RH.AIJ_FILIAL AND RS.AIJ_NROPOR=RH.AIJ_NROPOR AND RS.revision=RH.revision
),
PolicyHomologInPeriod AS (
    SELECT * FROM RevCycleRows WHERE homolog_date BETWEEN @date_start AND @date_end
),
FirstEngGlobal AS (
    SELECT A.AIJ_FILIAL, A.AIJ_NROPOR, MIN(A.AIJ_DTINIC) AS first_eng_global
    FROM AIJ010 A INNER JOIN EngSupport E ON E.AIJ_PROVEN=A.AIJ_PROVEN AND E.AIJ_STAGE=A.AIJ_STAGE
    WHERE A.D_E_L_E_T_='' AND ISNULL(A.AIJ_DTINIC,'')<>'' GROUP BY A.AIJ_FILIAL, A.AIJ_NROPOR
),
AnchorCurrent AS (
    SELECT A.AIJ_FILIAL, A.AIJ_NROPOR, A.AIJ_REVISA AS anchor_revision, A.AIJ_DTINIC AS anchor_date,
        ROW_NUMBER() OVER (PARTITION BY A.AIJ_FILIAL, A.AIJ_NROPOR ORDER BY A.AIJ_DTINIC DESC, A.AIJ_HRINIC DESC, A.R_E_C_N_O_ DESC) AS rn
    FROM AIJ010 A
    INNER JOIN Ad1Active AD1 ON AD1.AD1_FILIAL=A.AIJ_FILIAL AND AD1.AD1_NROPOR=A.AIJ_NROPOR AND AD1.AD1_REVISA=A.AIJ_REVISA
    INNER JOIN LmpAnchor L ON L.AIJ_PROVEN=A.AIJ_PROVEN AND L.AIJ_STAGE=A.AIJ_STAGE
    WHERE A.D_E_L_E_T_=''
),
PolicyCurrentOvLevel AS (
    SELECT AC.AIJ_FILIAL, AC.AIJ_NROPOR, AC.anchor_revision AS revision, AD1.sale_description,
        AC.anchor_date AS homolog_date, ISNULL(REM.eng_minutes_closed,0) AS eng_minutes_closed
    FROM AnchorCurrent AC
    INNER JOIN Ad1Active AD1 ON AD1.AD1_FILIAL=AC.AIJ_FILIAL AND AD1.AD1_NROPOR=AC.AIJ_NROPOR
    INNER JOIN FirstEngGlobal FE ON FE.AIJ_FILIAL=AC.AIJ_FILIAL AND FE.AIJ_NROPOR=AC.AIJ_NROPOR
    LEFT JOIN RevEngMinutes REM ON REM.AIJ_FILIAL=AC.AIJ_FILIAL AND REM.AIJ_NROPOR=AC.AIJ_NROPOR AND REM.revision=AC.anchor_revision
    WHERE AC.rn=1
      AND EXISTS (SELECT 1 FROM RevHomolog RH WHERE RH.AIJ_FILIAL=AC.AIJ_FILIAL AND RH.AIJ_NROPOR=AC.AIJ_NROPOR)
      AND (AC.anchor_date BETWEEN @date_start AND @date_end OR FE.first_eng_global BETWEEN @date_start AND @date_end)
)
SELECT row_kind, date_start, date_end, sale_number, branch, revision, current_revision,
    sale_description, homolog_date, rev_first_eng, eng_minutes_closed, has_sample_on_rev,
    tipo_proposto_strict, also_in_politica_atual_ov, metric_name, metric_value
FROM (
    SELECT 'TOTAL' AS row_kind, @date_start AS date_start, @date_end AS date_end,
        NULL AS sale_number, NULL AS branch, NULL AS revision, NULL AS current_revision,
        NULL AS sale_description, NULL AS homolog_date, NULL AS rev_first_eng, NULL AS eng_minutes_closed,
        NULL AS has_sample_on_rev, NULL AS tipo_proposto_strict, NULL AS also_in_politica_atual_ov,
        v.metric_name, v.metric_value
    FROM (VALUES
        ('dashboard_politica_atual_ov', CAST((SELECT COUNT(*) FROM PolicyCurrentOvLevel) AS VARCHAR(20))),
        ('dashboard_atual_residence30', CAST((SELECT COUNT(*) FROM PolicyCurrentOvLevel WHERE eng_minutes_closed>=30) AS VARCHAR(20))),
        ('proposta_homolog_por_revisao', CAST((SELECT COUNT(*) FROM PolicyHomologInPeriod) AS VARCHAR(20))),
        ('proposta_lmp_strict', CAST((SELECT COUNT(*) FROM PolicyHomologInPeriod WHERE tipo_proposto_strict='LMP') AS VARCHAR(20))),
        ('proposta_outro_strict', CAST((SELECT COUNT(*) FROM PolicyHomologInPeriod WHERE tipo_proposto_strict='OUTRO') AS VARCHAR(20))),
        ('ovs_distintas', CAST((SELECT COUNT(DISTINCT CONCAT(AIJ_FILIAL,':',AIJ_NROPOR)) FROM PolicyHomologInPeriod) AS VARCHAR(20))),
        ('linhas_extra_mesma_ov', CAST((SELECT COUNT(*) FROM PolicyHomologInPeriod)-(
            SELECT COUNT(DISTINCT CONCAT(AIJ_FILIAL,':',AIJ_NROPOR)) FROM PolicyHomologInPeriod) AS VARCHAR(20)))
    ) AS v(metric_name, metric_value)

    UNION ALL

    SELECT 'DETAIL_HOMOLOG_REV', @date_start, @date_end,
        RTRIM(P.AIJ_NROPOR), RTRIM(P.AIJ_FILIAL), P.revision, P.current_revision,
        P.sale_description, P.homolog_date, P.rev_first_eng, P.eng_minutes_closed,
        P.has_sample_on_rev, P.tipo_proposto_strict,
        CASE WHEN C.AIJ_NROPOR IS NOT NULL THEN 1 ELSE 0 END,
        NULL, NULL
    FROM PolicyHomologInPeriod P
    LEFT JOIN PolicyCurrentOvLevel C ON C.AIJ_FILIAL=P.AIJ_FILIAL AND C.AIJ_NROPOR=P.AIJ_NROPOR

    UNION ALL

    SELECT 'ONLY_CURRENT_OV', @date_start, @date_end,
        RTRIM(C.AIJ_NROPOR), RTRIM(C.AIJ_FILIAL), C.revision, NULL,
        C.sale_description, C.homolog_date, NULL, C.eng_minutes_closed,
        NULL, NULL, NULL, NULL, NULL
    FROM PolicyCurrentOvLevel C
    WHERE NOT EXISTS (
        SELECT 1 FROM PolicyHomologInPeriod P
        WHERE P.AIJ_FILIAL=C.AIJ_FILIAL AND P.AIJ_NROPOR=C.AIJ_NROPOR
          AND P.revision=C.revision AND P.homolog_date BETWEEN @date_start AND @date_end
    )
) X
ORDER BY
    CASE row_kind WHEN 'TOTAL' THEN 0 WHEN 'DETAIL_HOMOLOG_REV' THEN 1 ELSE 2 END,
    homolog_date, sale_number, revision, metric_name;
