/*
  Investigação DAVI-INVENTORY-ADJUSTMENT-REPORT — reverse engineering do
  relatório Protheus de ajustes de inventário (filial 02, 2026-09-04..29,
  armazéns 01+99, D3_DOC='INVENT').

  Objetivo: descobrir (a) regra entrada/saída, (b) origem de
  "custo médio do movimento" e "custo total" do relatório.

  Result sets (ordem):
    1) sx3_sd3_cost_fields      — campos SD3 com 'custo'/'medio'/'movimento'
    2) sx3_sb_cost_fields       — campos SB2/SB9 com 'custo'/'medio'
    3) tmcf_distribution        — TM/CF distinct no recorte + totais
    4) seqcalc_distribution     — D3_SEQCALC distinct no recorte
    5) window_movements         — as 45 linhas completas (custos + seqcalc)
    6) sample_unit_costs        — os 5 casos do briefing com custo unitário
    7) sb2_current              — SB2 atual dos produtos do recorte (filial 02)
    8) sb9_closures_f02         — datas de fechamento SB9 filial 02 (ago-out 2026)
    9) sb9_for_products         — SB9 dos produtos no fechamento mais próximo de set/2026
   10) sf5_tm_lookup            — SF5 para TM 499/999 (confirmar ausência TES)
   11) estorno_check            — D3_ESTORNO no recorte
*/
SET NOCOUNT ON;

DECLARE @f CHAR(2) = '02';
DECLARE @d0 CHAR(8) = '20260904';
DECLARE @d1 CHAR(8) = '20260930'; -- exclusiva

-- (1) Dicionário SD3: custo/médio/movimento/entrada/saída
SELECT X3_ARQUIVO, X3_ORDEM, RTRIM(X3_CAMPO) AS field, RTRIM(X3_TITULO) AS titulo, RTRIM(X3_DESCRIC) AS descricao
FROM SX3010 WITH (NOLOCK)
WHERE D_E_L_E_T_ = '' AND X3_ARQUIVO = 'SD3'
  AND (
    X3_TITULO LIKE '%usto%' OR X3_DESCRIC LIKE '%usto%'
    OR X3_TITULO LIKE '%ntrada%' OR X3_DESCRIC LIKE '%ntrada%'
    OR X3_TITULO LIKE '%a%da%' OR X3_DESCRIC LIKE '%a%da%'
    OR X3_CAMPO LIKE 'D3_%MOVA%' OR X3_CAMPO LIKE 'D3_SEQ%'
  )
ORDER BY X3_ORDEM;

-- (2) SB2/SB9 campos de custo
SELECT X3_ARQUIVO, X3_ORDEM, RTRIM(X3_CAMPO) AS field, RTRIM(X3_TITULO) AS titulo, RTRIM(X3_DESCRIC) AS descricao
FROM SX3010 WITH (NOLOCK)
WHERE D_E_L_E_T_ = '' AND X3_ARQUIVO IN ('SB2','SB9')
  AND (X3_CAMPO LIKE '%CM%' OR X3_CAMPO LIKE '%CUS%' OR X3_CAMPO LIKE '%V%T%'
       OR X3_TITULO LIKE '%usto%' OR X3_DESCRIC LIKE '%usto%')
ORDER BY X3_ARQUIVO, X3_ORDEM;

-- (3) TM/CF no recorte
SELECT RTRIM(D3_TM) AS tm, RTRIM(D3_CF) AS cf,
       COUNT(*) AS rows_n,
       SUM(D3_QUANT) AS sum_quant,
       SUM(D3_CUSTO1) AS sum_custo1
FROM SD3010 WITH (NOLOCK)
WHERE D_E_L_E_T_ = '' AND RTRIM(ISNULL(D3_ESTORNO,'')) <> 'S'
  AND RTRIM(LTRIM(D3_DOC)) = 'INVENT'
  AND D3_FILIAL = @f
  AND D3_EMISSAO >= @d0 AND D3_EMISSAO < @d1
  AND D3_LOCAL IN ('01','99')
GROUP BY D3_TM, D3_CF
ORDER BY D3_TM, D3_CF;

-- (4) D3_SEQCALC distinct no recorte
SELECT D3_SEQCALC AS seqcalc, COUNT(*) AS rows_n
FROM SD3010 WITH (NOLOCK)
WHERE D_E_L_E_T_ = '' AND RTRIM(ISNULL(D3_ESTORNO,'')) <> 'S'
  AND RTRIM(LTRIM(D3_DOC)) = 'INVENT'
  AND D3_FILIAL = @f
  AND D3_EMISSAO >= @d0 AND D3_EMISSAO < @d1
  AND D3_LOCAL IN ('01','99')
GROUP BY D3_SEQCALC ORDER BY D3_SEQCALC;

-- (5) As 45 linhas
SELECT D3_EMISSAO AS emissao, D3_FILIAL AS filial, RTRIM(D3_COD) AS cod,
       RTRIM(D3_LOCAL) AS local_, RTRIM(D3_DOC) AS doc,
       RTRIM(D3_TM) AS tm, RTRIM(D3_CF) AS cf,
       D3_QUANT AS quant, D3_CUSTO1 AS custo1,
       D3_CUSTO2 AS custo2, D3_CUSRP1 AS cusrp1, D3_CMRP AS cmrp,
       D3_CMFIXO AS cmfixo, D3_CUSFF1 AS cusff1,
       D3_SEQCALC AS seqcalc, RTRIM(D3_ESTORNO) AS estorno,
       RTRIM(D3_TEATF) AS teatf, SD3.R_E_C_N_O_ AS recno
FROM SD3010 SD3 WITH (NOLOCK)
WHERE D_E_L_E_T_ = '' AND RTRIM(ISNULL(D3_ESTORNO,'')) <> 'S'
  AND RTRIM(LTRIM(D3_DOC)) = 'INVENT'
  AND D3_FILIAL = @f
  AND D3_EMISSAO >= @d0 AND D3_EMISSAO < @d1
  AND D3_LOCAL IN ('01','99')
ORDER BY D3_EMISSAO, RTRIM(D3_COD), RTRIM(D3_LOCAL);

-- (6) Os 5 casos do briefing (detalhe)
SELECT D3_EMISSAO AS emissao, RTRIM(D3_COD) AS cod, RTRIM(D3_LOCAL) AS local_,
       RTRIM(D3_TM) AS tm, RTRIM(D3_CF) AS cf,
       D3_QUANT AS quant, D3_CUSTO1 AS custo1,
       CASE WHEN D3_QUANT <> 0 THEN D3_CUSTO1/D3_QUANT END AS unit_from_custo1,
       D3_CUSRP1 AS cusrp1, D3_CMRP AS cmrp, D3_CMFIXO AS cmfixo,
       D3_CUSFF1 AS cusff1, D3_SEQCALC AS seqcalc, SD3.R_E_C_N_O_ AS recno
FROM SD3010 SD3 WITH (NOLOCK)
WHERE D_E_L_E_T_ = '' AND RTRIM(ISNULL(D3_ESTORNO,'')) <> 'S'
  AND RTRIM(LTRIM(D3_DOC)) = 'INVENT' AND D3_FILIAL = @f
  AND (
    (D3_EMISSAO = '20260904' AND RTRIM(D3_COD)='10080422' AND RTRIM(D3_LOCAL) IN ('01','99'))
    OR (D3_EMISSAO = '20260929' AND RTRIM(D3_COD)='10400035' AND RTRIM(D3_LOCAL)='99')
    OR (D3_EMISSAO = '20260929' AND RTRIM(D3_COD)='10400039' AND RTRIM(D3_LOCAL)='99')
    OR (D3_EMISSAO = '20260928' AND RTRIM(D3_COD)='10500055' AND RTRIM(D3_LOCAL)='99')
  )
ORDER BY D3_EMISSAO, RTRIM(D3_COD), RTRIM(D3_LOCAL);

-- (7) SB2 atual dos produtos do recorte
SELECT SB2.B2_FILIAL AS filial, RTRIM(SB2.B2_COD) AS cod, RTRIM(SB2.B2_LOCAL) AS local_,
       SB2.B2_QATU AS qatu, SB2.B2_CM1 AS cm1, SB2.B2_VATU1 AS vatu1,
       SB2.B2_VFIM1 AS vfim1, SB2.B2_QFIM AS qfim
FROM SB2010 SB2 WITH (NOLOCK)
WHERE SB2.D_E_L_E_T_ = '' AND SB2.B2_FILIAL = @f
  AND RTRIM(SB2.B2_COD) IN (
    SELECT DISTINCT RTRIM(D3_COD) FROM SD3010 WITH (NOLOCK)
    WHERE D_E_L_E_T_ = '' AND RTRIM(LTRIM(D3_DOC))='INVENT'
      AND D3_FILIAL=@f AND D3_EMISSAO >= @d0 AND D3_EMISSAO < @d1
      AND D3_LOCAL IN ('01','99'))
ORDER BY RTRIM(SB2.B2_COD), RTRIM(SB2.B2_LOCAL);

-- (8) Datas de fechamento SB9 filial 02 (ago–out 2026)
SELECT B9_FILIAL AS filial, B9_DATA AS data_fechamento,
       COUNT(*) AS rows_n, SUM(B9_VINI1) AS vini1, SUM(B9_CUSTD) AS custd
FROM SB9010 WITH (NOLOCK)
WHERE D_E_L_E_T_ = '' AND B9_FILIAL = @f
  AND B9_DATA >= '20260801' AND B9_DATA <= '20261031'
GROUP BY B9_FILIAL, B9_DATA ORDER BY B9_DATA;

-- (9) SB9 dos produtos do recorte nos fechamentos de set/out
SELECT B9_FILIAL AS filial, RTRIM(B9_COD) AS cod, RTRIM(B9_LOCAL) AS local_,
       B9_DATA AS data_fechamento,
       B9_QINI AS qini, B9_VINI1 AS vini1,
       B9_CUSTD AS custd, B9_MCUSTD AS mcustd, B9_CM1 AS cm1, B9_CMRP1 AS cmrp1
FROM SB9010 WITH (NOLOCK)
WHERE D_E_L_E_T_ = '' AND B9_FILIAL = @f
  AND B9_DATA >= '20260801' AND B9_DATA <= '20261031'
  AND RTRIM(B9_COD) IN (
    SELECT DISTINCT RTRIM(D3_COD) FROM SD3010 WITH (NOLOCK)
    WHERE D_E_L_E_T_ = '' AND RTRIM(LTRIM(D3_DOC))='INVENT'
      AND D3_FILIAL=@f AND D3_EMISSAO >= @d0 AND D3_EMISSAO < @d1
      AND D3_LOCAL IN ('01','99'))
ORDER BY B9_DATA, RTRIM(B9_COD), RTRIM(B9_LOCAL);

-- (10) SF5: colunas disponíveis (provar ausência de TM 499/999)
SELECT COLUMN_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'SF5010'
ORDER BY ORDINAL_POSITION;

-- (11) D3_ESTORNO no recorte
SELECT RTRIM(D3_ESTORNO) AS estorno, COUNT(*) AS rows_n
FROM SD3010 WITH (NOLOCK)
WHERE D_E_L_E_T_ = '' AND RTRIM(LTRIM(D3_DOC)) = 'INVENT'
  AND D3_FILIAL = @f
  AND D3_EMISSAO >= @d0 AND D3_EMISSAO < @d1
  AND D3_LOCAL IN ('01','99')
GROUP BY D3_ESTORNO;
