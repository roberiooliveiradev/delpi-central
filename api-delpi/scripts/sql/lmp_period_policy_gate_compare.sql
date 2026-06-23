-- Gate de políticas LMP — simular ANTES de alterar LMPQueryRepository.
-- Comparar totais por política com controle RQ-060 (script validate_lmp_period_policies_vs_rq060.py).
-- Parâmetros: substituir @date_start / @date_end pelo script Python.
DECLARE @date_start CHAR(8) = '20260601';
DECLARE @date_end   CHAR(8) = '20260630';
DECLARE @min_eng_minutes INT = 30;

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
LmpFinalized AS (
    SELECT * FROM (VALUES
        ('000002', '000012'),
        ('000003', '000012')
    ) AS F(AIJ_PROVEN, AIJ_STAGE)
),
Ad1Active AS (
    SELECT
        AD1.AD1_FILIAL,
        AD1.AD1_NROPOR,
        AD1.AD1_REVISA,
        RTRIM(AD1.AD1_DESCRI) AS sale_description
    FROM AD1010 AD1
    WHERE AD1.D_E_L_E_T_ = ''
),
RevHomolog AS (
    SELECT
        A.AIJ_FILIAL,
        A.AIJ_NROPOR,
        A.AIJ_REVISA AS revision,
        MIN(A.AIJ_DTINIC) AS homolog_date
    FROM AIJ010 A
    INNER JOIN Ad1Active AD1
        ON AD1.AD1_FILIAL = A.AIJ_FILIAL
       AND AD1.AD1_NROPOR = A.AIJ_NROPOR
    INNER JOIN LmpFinalized F
        ON F.AIJ_PROVEN = A.AIJ_PROVEN
       AND F.AIJ_STAGE = A.AIJ_STAGE
    WHERE A.D_E_L_E_T_ = ''
    GROUP BY A.AIJ_FILIAL, A.AIJ_NROPOR, A.AIJ_REVISA
),
RevEngMinutes AS (
    SELECT
        A.AIJ_FILIAL,
        A.AIJ_NROPOR,
        A.AIJ_REVISA AS revision,
        MIN(A.AIJ_DTINIC) AS rev_first_eng,
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
    INNER JOIN EngSupport E
        ON E.AIJ_PROVEN = A.AIJ_PROVEN
       AND E.AIJ_STAGE = A.AIJ_STAGE
    WHERE A.D_E_L_E_T_ = ''
    GROUP BY A.AIJ_FILIAL, A.AIJ_NROPOR, A.AIJ_REVISA
),
RevAnchor AS (
    SELECT
        A.AIJ_FILIAL,
        A.AIJ_NROPOR,
        A.AIJ_REVISA AS revision,
        MIN(A.AIJ_DTINIC) AS anchor_date
    FROM AIJ010 A
    INNER JOIN LmpAnchor L
        ON L.AIJ_PROVEN = A.AIJ_PROVEN
       AND L.AIJ_STAGE = A.AIJ_STAGE
    WHERE A.D_E_L_E_T_ = ''
    GROUP BY A.AIJ_FILIAL, A.AIJ_NROPOR, A.AIJ_REVISA
),
RevCycleRows AS (
    SELECT
        RH.AIJ_FILIAL,
        RH.AIJ_NROPOR,
        RH.revision,
        AD1.sale_description,
        AD1.AD1_REVISA AS current_revision,
        RH.homolog_date,
        REM.rev_first_eng,
        ISNULL(REM.eng_minutes_closed, 0) AS eng_minutes_closed,
        RA.anchor_date,
        CASE
            WHEN ISNULL(REM.eng_minutes_closed, 0) >= @min_eng_minutes THEN 'LMP'
            ELSE 'OUTRO'
        END AS tipo_strict
    FROM RevHomolog RH
    INNER JOIN Ad1Active AD1
        ON AD1.AD1_FILIAL = RH.AIJ_FILIAL
       AND AD1.AD1_NROPOR = RH.AIJ_NROPOR
    LEFT JOIN RevEngMinutes REM
        ON REM.AIJ_FILIAL = RH.AIJ_FILIAL
       AND REM.AIJ_NROPOR = RH.AIJ_NROPOR
       AND REM.revision = RH.revision
    LEFT JOIN RevAnchor RA
        ON RA.AIJ_FILIAL = RH.AIJ_FILIAL
       AND RA.AIJ_NROPOR = RH.AIJ_NROPOR
       AND RA.revision = RH.revision
),
AnchorCurrent AS (
    SELECT
        A.AIJ_FILIAL,
        A.AIJ_NROPOR,
        A.AIJ_REVISA AS anchor_revision,
        A.AIJ_DTINIC AS anchor_date,
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
PolicyAnchorInPeriodOv AS (
    SELECT
        AC.AIJ_FILIAL,
        AC.AIJ_NROPOR,
        AC.anchor_revision AS revision,
        AC.anchor_date
    FROM AnchorCurrent AC
    WHERE AC.rn = 1
      AND AC.anchor_date BETWEEN @date_start AND @date_end
      AND EXISTS (
          SELECT 1
          FROM RevHomolog RH
          WHERE RH.AIJ_FILIAL = AC.AIJ_FILIAL
            AND RH.AIJ_NROPOR = AC.AIJ_NROPOR
      )
),
PolicyHomologRevInPeriod AS (
    SELECT *
    FROM RevCycleRows
    WHERE homolog_date BETWEEN @date_start AND @date_end
),
PolicyEngRevWorkMonth AS (
    SELECT *
    FROM RevCycleRows
    WHERE eng_minutes_closed >= @min_eng_minutes
      AND (
          rev_first_eng BETWEEN @date_start AND @date_end
          OR anchor_date BETWEEN @date_start AND @date_end
      )
),
PolicyEngRevFirstEngOnly AS (
    SELECT *
    FROM RevEngMinutes
    WHERE eng_minutes_closed >= @min_eng_minutes
      AND rev_first_eng BETWEEN @date_start AND @date_end
)
SELECT
    policy_name,
    row_kind,
    metric_name,
    metric_value,
    RTRIM(sale_number) AS sale_number,
    RTRIM(branch) AS branch,
    revision,
    homolog_date,
    rev_first_eng,
    anchor_date,
    eng_minutes_closed,
    tipo_strict
FROM (
    SELECT
        'anchor_in_period_ov' AS policy_name,
        'TOTAL' AS row_kind,
        v.metric_name,
        v.metric_value,
        NULL AS sale_number,
        NULL AS branch,
        NULL AS revision,
        NULL AS homolog_date,
        NULL AS rev_first_eng,
        NULL AS anchor_date,
        NULL AS eng_minutes_closed,
        NULL AS tipo_strict
    FROM (VALUES
        ('linhas', CAST((SELECT COUNT(*) FROM PolicyAnchorInPeriodOv) AS VARCHAR(20))),
        ('ovs_distintas', CAST((
            SELECT COUNT(DISTINCT CONCAT(AIJ_FILIAL, ':', AIJ_NROPOR))
            FROM PolicyAnchorInPeriodOv
        ) AS VARCHAR(20)))
    ) AS v(metric_name, metric_value)

    UNION ALL

    SELECT
        'anchor_in_period_ov',
        'DETAIL',
        NULL,
        NULL,
        P.AIJ_NROPOR,
        P.AIJ_FILIAL,
        P.revision,
        NULL,
        NULL,
        P.anchor_date,
        NULL,
        NULL
    FROM PolicyAnchorInPeriodOv P

    UNION ALL

    SELECT
        'homolog_rev_in_period',
        'TOTAL',
        v.metric_name,
        v.metric_value,
        NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL
    FROM (VALUES
        ('linhas', CAST((SELECT COUNT(*) FROM PolicyHomologRevInPeriod) AS VARCHAR(20))),
        ('linhas_lmp_30min', CAST((
            SELECT COUNT(*) FROM PolicyHomologRevInPeriod WHERE tipo_strict = 'LMP'
        ) AS VARCHAR(20))),
        ('ovs_distintas', CAST((
            SELECT COUNT(DISTINCT CONCAT(AIJ_FILIAL, ':', AIJ_NROPOR))
            FROM PolicyHomologRevInPeriod WHERE tipo_strict = 'LMP'
        ) AS VARCHAR(20)))
    ) AS v(metric_name, metric_value)

    UNION ALL

    SELECT
        'homolog_rev_in_period',
        'DETAIL',
        NULL,
        NULL,
        P.AIJ_NROPOR,
        P.AIJ_FILIAL,
        P.revision,
        P.homolog_date,
        P.rev_first_eng,
        P.anchor_date,
        CAST(P.eng_minutes_closed AS VARCHAR(20)),
        P.tipo_strict
    FROM PolicyHomologRevInPeriod P

    UNION ALL

    SELECT
        'eng_rev_work_month',
        'TOTAL',
        v.metric_name,
        v.metric_value,
        NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL
    FROM (VALUES
        ('linhas', CAST((SELECT COUNT(*) FROM PolicyEngRevWorkMonth) AS VARCHAR(20))),
        ('ovs_distintas', CAST((
            SELECT COUNT(DISTINCT CONCAT(AIJ_FILIAL, ':', AIJ_NROPOR))
            FROM PolicyEngRevWorkMonth
        ) AS VARCHAR(20)))
    ) AS v(metric_name, metric_value)

    UNION ALL

    SELECT
        'eng_rev_work_month',
        'DETAIL',
        NULL,
        NULL,
        P.AIJ_NROPOR,
        P.AIJ_FILIAL,
        P.revision,
        P.homolog_date,
        P.rev_first_eng,
        P.anchor_date,
        CAST(P.eng_minutes_closed AS VARCHAR(20)),
        P.tipo_strict
    FROM PolicyEngRevWorkMonth P

    UNION ALL

    SELECT
        'eng_rev_first_eng_only',
        'TOTAL',
        v.metric_name,
        v.metric_value,
        NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL
    FROM (VALUES
        ('linhas', CAST((SELECT COUNT(*) FROM PolicyEngRevFirstEngOnly) AS VARCHAR(20))),
        ('ovs_distintas', CAST((
            SELECT COUNT(DISTINCT CONCAT(AIJ_FILIAL, ':', AIJ_NROPOR))
            FROM PolicyEngRevFirstEngOnly
        ) AS VARCHAR(20)))
    ) AS v(metric_name, metric_value)

    UNION ALL

    SELECT
        'eng_rev_first_eng_only',
        'DETAIL',
        NULL,
        NULL,
        P.AIJ_NROPOR,
        P.AIJ_FILIAL,
        P.revision,
        NULL,
        P.rev_first_eng,
        NULL,
        CAST(P.eng_minutes_closed AS VARCHAR(20)),
        CASE WHEN P.eng_minutes_closed >= @min_eng_minutes THEN 'LMP' ELSE 'OUTRO' END
    FROM PolicyEngRevFirstEngOnly P
) X
ORDER BY
    policy_name,
    CASE row_kind WHEN 'TOTAL' THEN 0 ELSE 1 END,
    metric_name,
    sale_number,
    revision;
