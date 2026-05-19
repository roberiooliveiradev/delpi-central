/*
================================================================================
DIAGNÓSTICO LMP x AMOSTRA — Protheus (AIJ010 / AD1010)
================================================================================
Objetivo: descobrir por que OVs de amostra entram como LMP na API.

Regras ATUAIS no backend (lmp_query_settings.py):
  LMP âncora:
    processo 000002 + estágio 000003, 000012
    processo 000003 + estágio 000003, 000012
  Amostra âncora:
    processo 000003 + estágio 000002, 000008

Regra de prioridade na listagem (após correção):
  - Se a OV já teve estágio 000012 (lançamento/homologação LMP) → sempre LMP.
  - Senão: evento âncora LMP ou amostra mais recente; em empate, amostra prevalece.
  - Amostra âncora inclui 000002+000008 e 000003+000002/000008.

Hipótese comum de erro (corrigida):
  - OV com histórico 000008 (amostra) e 000012 (LMP homologada) na mesma data:
    a regra antiga “última âncora” classificava como AMOSTRA; 000012 deve fixar LMP.
  - Amostra “real” (ex. 003380): tem 000008 mas ainda NÃO passou por 000012.

Como usar:
  1) Ajuste @FILIAL, @DATE_START, @DATE_END (e opcional @NROPOR).
  2) Rode o bloco (1) resumo por OV.
  3) Rode o bloco (2) para uma OV suspeita (detalhe de eventos).
  4) Rode o bloco (3) para ver combinações processo+estágio no período.
================================================================================
*/

DECLARE @FILIAL     CHAR(2)  = '01';          -- NULL = filiais 01 e 02
DECLARE @DATE_START CHAR(8)  = '20250101';    -- YYYYMMDD ou NULL
DECLARE @DATE_END   CHAR(8)  = '20260519';    -- YYYYMMDD ou NULL
DECLARE @NROPOR     VARCHAR(20) = NULL;       -- ex: '000123' ou NULL = todas

/* ============================================================================
   (1) RESUMO POR OV — classificação igual à API
   ============================================================================ */
WITH
EventosClassificados AS (
    SELECT
        A.AIJ_FILIAL,
        A.AIJ_NROPOR,
        A.AIJ_REVISA,
        A.AIJ_PROVEN,
        A.AIJ_STAGE,
        A.AIJ_DTINIC,
        A.AIJ_HRINIC,
        A.AIJ_DTENCE,
        A.AIJ_HRENCE,
        A.R_E_C_N_O_,
        CASE
            WHEN (A.AIJ_PROVEN = '000002' AND A.AIJ_STAGE IN ('000003', '000012'))
              OR (A.AIJ_PROVEN = '000003' AND A.AIJ_STAGE IN ('000003', '000012'))
            THEN 1 ELSE 0
        END AS IS_LMP_ANCHOR,
        CASE
            WHEN A.AIJ_PROVEN = '000003' AND A.AIJ_STAGE IN ('000002', '000008')
            THEN 1 ELSE 0
        END AS IS_SAMPLE_ANCHOR_CONFIG_ATUAL,
        /* amostra no processo oportunidade (doc) — NÃO está na config hoje */
        CASE
            WHEN A.AIJ_PROVEN = '000002' AND A.AIJ_STAGE = '000008'
            THEN 1 ELSE 0
        END AS IS_AMOSTRA_DOC_000002_000008,
        CASE
            WHEN (A.AIJ_PROVEN = '000002' AND A.AIJ_STAGE IN ('000003', '000008', '000012'))
              OR (A.AIJ_PROVEN = '000003' AND A.AIJ_STAGE IN ('000003', '000012'))
            THEN 1 ELSE 0
        END AS IS_ENG_SUPPORT
    FROM AIJ010 A
    WHERE A.D_E_L_E_T_ = ''
      AND (
            (@FILIAL IS NULL AND A.AIJ_FILIAL IN ('01', '02'))
            OR (A.AIJ_FILIAL = @FILIAL)
          )
      AND (@NROPOR IS NULL OR A.AIJ_NROPOR = @NROPOR)
),

LMPAnchorEventos AS (
    SELECT
        E.*,
        ROW_NUMBER() OVER (
            PARTITION BY E.AIJ_FILIAL, E.AIJ_NROPOR
            ORDER BY E.AIJ_REVISA DESC, E.AIJ_DTINIC DESC, E.AIJ_HRINIC DESC, E.R_E_C_N_O_ DESC
        ) AS RN_DESC
    FROM EventosClassificados E
    WHERE E.IS_LMP_ANCHOR = 1
),

SampleAnchorEventos AS (
    SELECT
        E.*,
        ROW_NUMBER() OVER (
            PARTITION BY E.AIJ_FILIAL, E.AIJ_NROPOR
            ORDER BY E.AIJ_REVISA DESC, E.AIJ_DTINIC DESC, E.AIJ_HRINIC DESC, E.R_E_C_N_O_ DESC
        ) AS RN_DESC
    FROM EventosClassificados E
    WHERE E.IS_SAMPLE_ANCHOR_CONFIG_ATUAL = 1
),

LMPEventos AS (
    SELECT
        A.AIJ_FILIAL,
        A.AIJ_NROPOR,
        A.AIJ_PROVEN AS LMP_ANCHOR_PROVEN,
        A.AIJ_STAGE AS LMP_ANCHOR_STAGE,
        A.AIJ_DTINIC AS LMP_START_DATE,
        COALESCE(NULLIF(A.AIJ_DTENCE, ''), '') AS LMP_END_DATE
    FROM LMPAnchorEventos A
    WHERE A.RN_DESC = 1
),

SampleEventos AS (
    SELECT
        A.AIJ_FILIAL,
        A.AIJ_NROPOR,
        A.AIJ_PROVEN AS SAMPLE_ANCHOR_PROVEN,
        A.AIJ_STAGE AS SAMPLE_ANCHOR_STAGE,
        A.AIJ_DTINIC AS SAMPLE_START_DATE,
        COALESCE(NULLIF(A.AIJ_DTENCE, ''), '') AS SAMPLE_END_DATE
    FROM SampleAnchorEventos A
    WHERE A.RN_DESC = 1
),

HistoricoResumo AS (
    SELECT
        E.AIJ_FILIAL,
        E.AIJ_NROPOR,
        MAX(E.IS_LMP_ANCHOR) AS TEM_EVENTO_LMP_ANCHOR,
        MAX(E.IS_SAMPLE_ANCHOR_CONFIG_ATUAL) AS TEM_EVENTO_SAMPLE_CONFIG,
        MAX(E.IS_AMOSTRA_DOC_000002_000008) AS TEM_AMOSTRA_000002_000008,
        MAX(E.IS_ENG_SUPPORT) AS TEM_ENG_SUPPORT,
        COUNT(*) AS QTD_EVENTOS_HIST
    FROM EventosClassificados E
    GROUP BY E.AIJ_FILIAL, E.AIJ_NROPOR
),

ClassificacaoAPI AS (
    SELECT
        AD1.AD1_FILIAL,
        AD1.AD1_NROPOR,
        AD1.AD1_DESCRI,
        L.LMP_ANCHOR_PROVEN,
        L.LMP_ANCHOR_STAGE,
        L.LMP_START_DATE,
        L.LMP_END_DATE,
        S.SAMPLE_ANCHOR_PROVEN,
        S.SAMPLE_ANCHOR_STAGE,
        S.SAMPLE_START_DATE,
        S.SAMPLE_END_DATE,
        H.TEM_EVENTO_LMP_ANCHOR,
        H.TEM_EVENTO_SAMPLE_CONFIG,
        H.TEM_AMOSTRA_000002_000008,
        CASE
            WHEN L.AIJ_NROPOR IS NOT NULL THEN 'LMP'
            WHEN S.AIJ_NROPOR IS NOT NULL THEN 'AMOSTRA'
            ELSE NULL
        END AS LISTING_KIND_API,
        CASE
            WHEN H.TEM_AMOSTRA_000002_000008 = 1 AND L.AIJ_NROPOR IS NOT NULL
            THEN 'SUSPEITO: amostra 000002/000008 + LMP âncora na mesma OV'
            WHEN H.TEM_EVENTO_SAMPLE_CONFIG = 1 AND L.AIJ_NROPOR IS NOT NULL
            THEN 'SUSPEITO: amostra 000003 configurada + LMP âncora (prioridade LMP)'
            WHEN H.TEM_AMOSTRA_000002_000008 = 1 AND L.AIJ_NROPOR IS NULL AND S.AIJ_NROPOR IS NULL
            THEN 'SUSPEITO: amostra 000002/000008 mas fora da config de amostra'
            WHEN S.AIJ_NROPOR IS NOT NULL AND L.AIJ_NROPOR IS NULL
            THEN 'OK: só amostra (config atual)'
            WHEN L.AIJ_NROPOR IS NOT NULL AND S.AIJ_NROPOR IS NULL
            THEN 'OK: só LMP'
            ELSE 'SEM_CLASSIFICACAO'
        END AS DIAGNOSTICO
    FROM AD1010 AD1
    LEFT JOIN LMPEventos L
        ON L.AIJ_FILIAL = AD1.AD1_FILIAL AND L.AIJ_NROPOR = AD1.AD1_NROPOR
    LEFT JOIN SampleEventos S
        ON S.AIJ_FILIAL = AD1.AD1_FILIAL AND S.AIJ_NROPOR = AD1.AD1_NROPOR
    LEFT JOIN HistoricoResumo H
        ON H.AIJ_FILIAL = AD1.AD1_FILIAL AND H.AIJ_NROPOR = AD1.AD1_NROPOR
    WHERE AD1.D_E_L_E_T_ = ''
      AND (
            (@FILIAL IS NULL AND AD1.AD1_FILIAL IN ('01', '02'))
            OR (AD1.AD1_FILIAL = @FILIAL)
          )
      AND (@NROPOR IS NULL OR AD1.AD1_NROPOR = @NROPOR)
      AND (
            L.AIJ_NROPOR IS NOT NULL
            OR S.AIJ_NROPOR IS NOT NULL
            OR H.TEM_AMOSTRA_000002_000008 = 1
      )
)

SELECT
    C.AD1_FILIAL AS branch,
    C.AD1_NROPOR AS sale_number,
    C.AD1_DESCRI AS sale_description,
    C.LISTING_KIND_API AS listing_kind,
    C.DIAGNOSTICO,
    C.LMP_ANCHOR_PROVEN,
    C.LMP_ANCHOR_STAGE,
    C.LMP_START_DATE,
    C.SAMPLE_ANCHOR_PROVEN,
    C.SAMPLE_ANCHOR_STAGE,
    C.SAMPLE_START_DATE,
    C.TEM_AMOSTRA_000002_000008
FROM ClassificacaoAPI C
WHERE (
        @DATE_START IS NULL
        OR @DATE_END IS NULL
        OR COALESCE(C.LMP_START_DATE, C.SAMPLE_START_DATE, '') BETWEEN @DATE_START AND @DATE_END
      )
ORDER BY
    CASE WHEN C.DIAGNOSTICO LIKE 'SUSPEITO%' THEN 0 ELSE 1 END,
    COALESCE(C.LMP_START_DATE, C.SAMPLE_START_DATE) DESC,
    C.AD1_NROPOR DESC;


/* ============================================================================
   (2) DETALHE DE EVENTOS — uma OV (preencha @NROPOR acima)
   ============================================================================ */
/*
SELECT
    A.AIJ_FILIAL,
    A.AIJ_NROPOR,
    A.AIJ_REVISA,
    A.AIJ_PROVEN,
    A.AIJ_STAGE,
    A.AIJ_DTINIC,
    A.AIJ_HRINIC,
    A.AIJ_DTENCE,
    CASE
        WHEN (A.AIJ_PROVEN = '000002' AND A.AIJ_STAGE IN ('000003', '000012'))
          OR (A.AIJ_PROVEN = '000003' AND A.AIJ_STAGE IN ('000003', '000012'))
        THEN 'LMP'
        WHEN A.AIJ_PROVEN = '000003' AND A.AIJ_STAGE IN ('000002', '000008')
        THEN 'AMOSTRA_CFG'
        WHEN A.AIJ_PROVEN = '000002' AND A.AIJ_STAGE = '000008'
        THEN 'AMOSTRA_DOC_000002'
        ELSE ''
    END AS tipo_evento,
    A.R_E_C_N_O_
FROM AIJ010 A
WHERE A.D_E_L_E_T_ = ''
  AND A.AIJ_FILIAL = @FILIAL
  AND A.AIJ_NROPOR = @NROPOR
ORDER BY
    A.AIJ_REVISA,
    A.AIJ_DTINIC,
    A.AIJ_HRINIC,
    A.AIJ_STAGE,
    A.R_E_C_N_O_;
*/


/* ============================================================================
   (3) COMBINAÇÕES processo + estágio no período (descobrir regra real)
   ============================================================================ */
/*
SELECT
    A.AIJ_PROVEN AS processo,
    A.AIJ_STAGE AS estagio,
    COUNT(DISTINCT CONCAT(A.AIJ_FILIAL, '|', A.AIJ_NROPOR)) AS qtd_ov,
    CASE
        WHEN (A.AIJ_PROVEN = '000002' AND A.AIJ_STAGE IN ('000003', '000012'))
          OR (A.AIJ_PROVEN = '000003' AND A.AIJ_STAGE IN ('000003', '000012'))
        THEN 'LMP'
        WHEN A.AIJ_PROVEN = '000003' AND A.AIJ_STAGE IN ('000002', '000008')
        THEN 'AMOSTRA_CFG'
        WHEN A.AIJ_PROVEN = '000002' AND A.AIJ_STAGE = '000008'
        THEN 'AMOSTRA_DOC_000002'
        ELSE 'OUTRO'
    END AS classificacao
FROM AIJ010 A
WHERE A.D_E_L_E_T_ = ''
  AND A.AIJ_FILIAL = @FILIAL
  AND (@DATE_START IS NULL OR A.AIJ_DTINIC >= @DATE_START)
  AND (@DATE_END IS NULL OR A.AIJ_DTINIC <= @DATE_END)
GROUP BY
    A.AIJ_PROVEN,
    A.AIJ_STAGE,
    CASE
        WHEN (A.AIJ_PROVEN = '000002' AND A.AIJ_STAGE IN ('000003', '000012'))
          OR (A.AIJ_PROVEN = '000003' AND A.AIJ_STAGE IN ('000003', '000012'))
        THEN 'LMP'
        WHEN A.AIJ_PROVEN = '000003' AND A.AIJ_STAGE IN ('000002', '000008')
        THEN 'AMOSTRA_CFG'
        WHEN A.AIJ_PROVEN = '000002' AND A.AIJ_STAGE = '000008'
        THEN 'AMOSTRA_DOC_000002'
        ELSE 'OUTRO'
    END
ORDER BY qtd_ov DESC, processo, estagio;
*/


/* ============================================================================
   (4) TESTE DA QUERY UNIFICADA (igual CandidateLMPs da API)
   ============================================================================ */
/*
WITH
LMPAnchorEventos AS (
    SELECT A.AIJ_FILIAL, A.AIJ_NROPOR, A.AIJ_REVISA, A.AIJ_PROVEN, A.AIJ_STAGE,
           A.AIJ_DTINIC, A.AIJ_HRINIC, A.AIJ_DTENCE, A.R_E_C_N_O_,
           ROW_NUMBER() OVER (
               PARTITION BY A.AIJ_FILIAL, A.AIJ_NROPOR
               ORDER BY A.AIJ_REVISA DESC, A.AIJ_DTINIC DESC, A.AIJ_HRINIC DESC, A.R_E_C_N_O_ DESC
           ) AS RN_DESC
    FROM AIJ010 A
    WHERE A.D_E_L_E_T_ = ''
      AND A.AIJ_FILIAL = @FILIAL
      AND (
            (A.AIJ_PROVEN = '000002' AND A.AIJ_STAGE IN ('000003', '000012'))
            OR (A.AIJ_PROVEN = '000003' AND A.AIJ_STAGE IN ('000003', '000012'))
          )
),
LMPEventos AS (
    SELECT A.AIJ_FILIAL, A.AIJ_NROPOR, A.AIJ_DTINIC AS LMP_START_DATE
    FROM LMPAnchorEventos A WHERE A.RN_DESC = 1
),
SampleAnchorEventos AS (
    SELECT A.AIJ_FILIAL, A.AIJ_NROPOR, A.AIJ_PROVEN, A.AIJ_STAGE, A.AIJ_DTINIC,
           ROW_NUMBER() OVER (
               PARTITION BY A.AIJ_FILIAL, A.AIJ_NROPOR
               ORDER BY A.AIJ_REVISA DESC, A.AIJ_DTINIC DESC, A.AIJ_HRINIC DESC, A.R_E_C_N_O_ DESC
           ) AS RN_DESC
    FROM AIJ010 A
    WHERE A.D_E_L_E_T_ = ''
      AND A.AIJ_FILIAL = @FILIAL
      AND A.AIJ_PROVEN = '000003' AND A.AIJ_STAGE IN ('000002', '000008')
),
SampleEventos AS (
    SELECT A.AIJ_FILIAL, A.AIJ_NROPOR, A.AIJ_DTINIC AS SAMPLE_START_DATE
    FROM SampleAnchorEventos A WHERE A.RN_DESC = 1
),
CandidateLMPs AS (
    SELECT AD1.AD1_FILIAL, AD1.AD1_NROPOR, AD1.AD1_DESCRI,
           'LMP' AS LISTING_KIND, L.LMP_START_DATE
    FROM AD1010 AD1
    INNER JOIN LMPEventos L ON L.AIJ_FILIAL = AD1.AD1_FILIAL AND L.AIJ_NROPOR = AD1.AD1_NROPOR
    WHERE AD1.D_E_L_E_T_ = '' AND AD1.AD1_FILIAL = @FILIAL
      AND (@DATE_START IS NULL OR L.LMP_START_DATE >= @DATE_START)
      AND (@DATE_END IS NULL OR L.LMP_START_DATE <= @DATE_END)

    UNION ALL

    SELECT AD1.AD1_FILIAL, AD1.AD1_NROPOR, AD1.AD1_DESCRI,
           'AMOSTRA' AS LISTING_KIND, S.SAMPLE_START_DATE AS LMP_START_DATE
    FROM AD1010 AD1
    INNER JOIN SampleEventos S ON S.AIJ_FILIAL = AD1.AD1_FILIAL AND S.AIJ_NROPOR = AD1.AD1_NROPOR
    WHERE AD1.D_E_L_E_T_ = ''
      AND AD1.AD1_FILIAL = @FILIAL
      AND NOT EXISTS (
          SELECT 1 FROM LMPEventos L2
          WHERE L2.AIJ_FILIAL = AD1.AD1_FILIAL AND L2.AIJ_NROPOR = AD1.AD1_NROPOR
      )
      AND (@DATE_START IS NULL OR S.SAMPLE_START_DATE >= @DATE_START)
      AND (@DATE_END IS NULL OR S.SAMPLE_START_DATE <= @DATE_END)
)
SELECT * FROM CandidateLMPs
WHERE @NROPOR IS NULL OR AD1_NROPOR = @NROPOR
ORDER BY LMP_START_DATE DESC;
*/
