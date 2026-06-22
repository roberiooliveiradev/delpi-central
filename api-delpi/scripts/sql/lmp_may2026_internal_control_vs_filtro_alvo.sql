-- Cruzamento explícito: 17 pastas INTERNAL_CONTROL (maio/2026) × filtro alvo
-- Filtro alvo = evento listing no mês + residence >= 30 min + homologação LMP
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
PeriodActivity AS (
    SELECT
        A.AIJ_FILIAL,
        A.AIJ_NROPOR,
        MIN(A.AIJ_DTINIC) AS activity_start
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
        A.AIJ_DTINIC AS anchor_start,
        A.AIJ_STAGE AS anchor_stage,
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
FiltroAlvo AS (
    SELECT
        AD1.AD1_NROPOR AS sale_number,
        RTRIM(AD1.AD1_FILIAL) AS branch,
        RTRIM(AD1.AD1_DESCRI) AS sale_description,
        PA.activity_start,
        AC.anchor_start,
        AC.anchor_stage,
        ISNULL(EM.eng_minutes_closed, 0) AS eng_minutes_closed
    FROM Ad1Active AD1
    INNER JOIN PeriodActivity PA
        ON PA.AIJ_FILIAL = AD1.AD1_FILIAL
       AND PA.AIJ_NROPOR = AD1.AD1_NROPOR
    INNER JOIN AnchorChosen AC
        ON AC.AIJ_FILIAL = AD1.AD1_FILIAL
       AND AC.AIJ_NROPOR = AD1.AD1_NROPOR
    INNER JOIN HasLmpFinalized LF
        ON LF.AIJ_FILIAL = AD1.AD1_FILIAL
       AND LF.AIJ_NROPOR = AD1.AD1_NROPOR
    INNER JOIN EngMinutesClosed EM
        ON EM.AIJ_FILIAL = AD1.AD1_FILIAL
       AND EM.AIJ_NROPOR = AD1.AD1_NROPOR
    WHERE EM.eng_minutes_closed >= 30
),
-- INTERNAL_CONTROL + HYPOTHESIS_MAP (072 26: candidatos 000090 / 000094)
InternalControlHypothesis AS (
    SELECT * FROM (VALUES
        ('070 26', 'flextronic',     '20260504', '003562', 1),
        ('071 26', '3RHO',           '20260504', '003403', 1),
        ('072 26', 'WEG Linhares',   '20260506', '000090', 1),
        ('072 26', 'WEG Linhares',   '20260506', '000094', 2),
        ('073 26', 'Wanke',          '20260508', '000088', 1),
        ('073 26', 'Wanke',          '20260508', '000089', 2),
        ('073 26', 'Wanke',          '20260508', '000095', 3),
        ('074 26', 'Weg Motores',    '20260508', '003568', 1),
        ('075 26', 'WEG Linhares',   '20260512', '000111', 1),
        ('076 26', 'WEG Linhares',   '20260513', '000084', 1),
        ('077 26', 'WEG Linhares',   '20260514', '003571', 1),
        ('078 26', 'Buhler',         '20260514', '003578', 1),
        ('079 26', 'WEG Linhares',   '20260515', '000090', 1),
        ('080 26', 'WEG Linhares',   '20260519', '003551', 1),
        ('081 26', 'WEG Linhares',   '20260520', '000054', 1),
        ('082 26', 'WEG Linhares',   '20260522', '000120', 1),
        ('083 26', 'WEG Energia',    '20260525', '003572', 1),
        ('084 26', 'WEG Energia',    '20260525', '003573', 1),
        ('085 26', 'WEG Energia',    '20260525', '003574', 1),
        ('086 26', 'WEG Linhares',   '20260525', '000097', 1)
    ) AS IC(folder_code, client, control_open, hypothesis_ov, hypothesis_rank)
),
FolderFiltroHits AS (
    SELECT
        IC.folder_code,
        IC.client,
        IC.control_open,
        IC.hypothesis_ov,
        IC.hypothesis_rank,
        CASE WHEN FA.sale_number IS NOT NULL THEN 1 ELSE 0 END AS no_filtro_alvo,
        FA.branch,
        FA.sale_description,
        FA.activity_start,
        FA.anchor_start,
        FA.anchor_stage,
        FA.eng_minutes_closed
    FROM InternalControlHypothesis IC
    LEFT JOIN FiltroAlvo FA
        ON FA.sale_number = IC.hypothesis_ov
),
FolderSummary AS (
    SELECT
        folder_code,
        MIN(client) AS client,
        MIN(control_open) AS control_open,
        COUNT(*) AS hypothesis_count,
        SUM(no_filtro_alvo) AS ovs_no_filtro,
        STRING_AGG(
            CASE WHEN no_filtro_alvo = 1 THEN hypothesis_ov END,
            ', '
        ) WITHIN GROUP (ORDER BY hypothesis_rank) AS ovs_batem,
        STRING_AGG(
            CASE WHEN no_filtro_alvo = 0 THEN hypothesis_ov END,
            ', '
        ) WITHIN GROUP (ORDER BY hypothesis_rank) AS ovs_ausentes_filtro
    FROM FolderFiltroHits
    GROUP BY folder_code
)
SELECT
    FS.folder_code,
    FS.client,
    FS.control_open,
    FS.hypothesis_count,
    FS.ovs_no_filtro,
    FS.ovs_batem,
    FS.ovs_ausentes_filtro,
    CASE
        WHEN FS.ovs_no_filtro = 0 THEN 'SEM_MATCH'
        WHEN FS.hypothesis_count = 1 AND FS.ovs_no_filtro = 1 THEN '1:1'
        WHEN FS.hypothesis_count > 1 AND FS.ovs_no_filtro = 1 THEN '1:1_CANDIDATO_UNICO'
        WHEN FS.hypothesis_count > 1 AND FS.ovs_no_filtro > 1 THEN '1:N_PASTA_MULTI_OV'
        ELSE 'PARCIAL'
    END AS match_tipo
FROM FolderSummary FS
ORDER BY FS.folder_code;
