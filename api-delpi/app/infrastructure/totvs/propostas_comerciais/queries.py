"""Consultas read-only de propostas comerciais (TOTVS/Protheus)."""

from __future__ import annotations

_COMMON_JOINS = """
FROM ADY010 ADY WITH (NOLOCK)
LEFT JOIN AD1010 AD1 WITH (NOLOCK)
  ON AD1.D_E_L_E_T_ <> '*'
 AND AD1.AD1_NROPOR = ADY.ADY_OPORTU
 AND AD1.AD1_REVISA = ADY.ADY_REVISA
LEFT JOIN SA1010 A1 WITH (NOLOCK)
  ON A1.D_E_L_E_T_ <> '*'
 AND A1.A1_COD = ADY.ADY_CLIENT
 AND A1.A1_LOJA = ADY.ADY_LOJENT
LEFT JOIN SUS010 SUS WITH (NOLOCK)
  ON SUS.D_E_L_E_T_ <> '*'
 AND SUS.US_COD = AD1.AD1_PROSPE
 AND SUS.US_LOJA = AD1.AD1_LOJPRO
LEFT JOIN SU5010 U5 WITH (NOLOCK)
  ON U5.D_E_L_E_T_ <> '*'
 AND U5.U5_CODCONT = COALESCE(NULLIF(RTRIM(ADY.ADY_CNTPRO), ''), AD1.AD1_CNTPRO)
LEFT JOIN SQB010 QB WITH (NOLOCK)
  ON QB.D_E_L_E_T_ <> '*'
 AND QB.QB_DEPTO = U5.U5_DEPTO
LEFT JOIN SE4010 E4 WITH (NOLOCK)
  ON E4.D_E_L_E_T_ <> '*'
 AND E4.E4_CODIGO = ADY.ADY_CONDPG
LEFT JOIN SA3010 A3 WITH (NOLOCK)
  ON A3.D_E_L_E_T_ <> '*'
 AND A3.A3_COD = ADY.ADY_VEND
LEFT JOIN SUM010 UM WITH (NOLOCK)
  ON UM.D_E_L_E_T_ <> '*'
 AND UM.UM_CARGO = A3.A3_CARGO
LEFT JOIN SYS_COMPANY CO WITH (NOLOCK)
  ON RTRIM(CO.M0_CODFIL) = RTRIM(COALESCE(NULLIF(RTRIM(ADY.ADY_FILIAL), ''), AD1.AD1_FILIAL))
 AND RTRIM(CO.M0_CODIGO) = '01'
"""

LIST_ACTIVE_RECENT_SQL = f"""
SELECT TOP (?)
    ADY.ADY_PROPOS AS proposta_interna,
    ADY.ADY_OPORTU AS oportunidade,
    ADY.ADY_PREVIS AS versao,
    ADY.ADY_DATA AS data_proposta,
    COALESCE(
        NULLIF(LTRIM(RTRIM(A1.A1_NOME)), ''),
        NULLIF(LTRIM(RTRIM(SUS.US_NOME)), '')
    ) AS cliente_nome,
    RTRIM(COALESCE(NULLIF(RTRIM(ADY.ADY_FILIAL), ''), AD1.AD1_FILIAL)) AS filial,
    (
        SELECT COUNT(1)
        FROM ADZ010 ADZ WITH (NOLOCK)
        WHERE ADZ.D_E_L_E_T_ <> '*'
          AND ADZ.ADZ_PROPOS = ADY.ADY_PROPOS
          AND ADZ.ADZ_REVISA = ADY.ADY_PREVIS
    ) AS quantidade_itens
{_COMMON_JOINS}
WHERE ADY.D_E_L_E_T_ <> '*'
  AND ADY.ADY_STATUS = 'A'
ORDER BY ADY.ADY_DATA DESC, ADY.ADY_PROPOS DESC, ADY.ADY_PREVIS DESC
"""

DETAIL_HEADER_SQL = f"""
SELECT TOP 1
    ADY.ADY_PROPOS AS proposta_interna,
    ADY.ADY_PREVIS AS versao,
    ADY.ADY_OPORTU AS oportunidade,
    ADY.ADY_REVISA AS revisao_oportunidade,
    ADY.ADY_DATA AS data_proposta,
    ADY.ADY_VALID AS validade_dias,
    ADY.ADY_STATUS AS status,
    RTRIM(COALESCE(NULLIF(RTRIM(ADY.ADY_FILIAL), ''), AD1.AD1_FILIAL)) AS filial,
    COALESCE(NULLIF(RTRIM(ADY.ADY_CNTPRO), ''), AD1.AD1_CNTPRO) AS contato_codigo,
    COALESCE(
        NULLIF(LTRIM(RTRIM(A1.A1_COD)), ''),
        NULLIF(LTRIM(RTRIM(SUS.US_COD)), '')
    ) AS cliente_codigo,
    COALESCE(
        NULLIF(LTRIM(RTRIM(A1.A1_LOJA)), ''),
        NULLIF(LTRIM(RTRIM(SUS.US_LOJA)), '')
    ) AS cliente_loja,
    ADY.ADY_VEND AS vendedor_codigo,
    ADY.ADY_CONDPG AS condicao_codigo,
    ADY.ADY_PICMS AS icms,
    ADY.ADY_PIPI AS ipi,
    ADY.ADY_FRETE AS frete,
    ADY.ADY_EMBALA AS embalagem,
    REPLACE(TRY_CONVERT(VARCHAR(MAX), ADY.ADY_OBS), CHAR(0), '') AS observacoes,
    COALESCE(
        NULLIF(LTRIM(RTRIM(A1.A1_NOME)), ''),
        NULLIF(LTRIM(RTRIM(SUS.US_NOME)), '')
    ) AS cliente_nome,
    COALESCE(
        NULLIF(LTRIM(RTRIM(A1.A1_NREDUZ)), ''),
        NULLIF(LTRIM(RTRIM(SUS.US_NREDUZ)), '')
    ) AS cliente_nome_fantasia,
    COALESCE(
        NULLIF(LTRIM(RTRIM(A1.A1_CGC)), ''),
        NULLIF(LTRIM(RTRIM(SUS.US_CGC)), '')
    ) AS cliente_cnpj,
    COALESCE(
        NULLIF(LTRIM(RTRIM(A1.A1_INSCR)), ''),
        NULLIF(LTRIM(RTRIM(SUS.US_INSCR)), '')
    ) AS cliente_ie,
    COALESCE(
        NULLIF(LTRIM(RTRIM(A1.A1_END)), ''),
        NULLIF(LTRIM(RTRIM(SUS.US_END)), '')
    ) AS cliente_endereco,
    COALESCE(
        NULLIF(LTRIM(RTRIM(A1.A1_BAIRRO)), ''),
        NULLIF(LTRIM(RTRIM(SUS.US_BAIRRO)), '')
    ) AS cliente_bairro,
    COALESCE(
        NULLIF(LTRIM(RTRIM(A1.A1_MUN)), ''),
        NULLIF(LTRIM(RTRIM(SUS.US_MUN)), '')
    ) AS cliente_cidade,
    COALESCE(
        NULLIF(LTRIM(RTRIM(A1.A1_EST)), ''),
        NULLIF(LTRIM(RTRIM(SUS.US_EST)), '')
    ) AS cliente_uf,
    COALESCE(
        NULLIF(LTRIM(RTRIM(A1.A1_CEP)), ''),
        NULLIF(LTRIM(RTRIM(SUS.US_CEP)), '')
    ) AS cliente_cep,
    CASE
        WHEN NULLIF(LTRIM(RTRIM(A1.A1_COD)), '') IS NOT NULL THEN A1.A1_TEL
        WHEN NULLIF(LTRIM(RTRIM(SUS.US_COD)), '') IS NOT NULL THEN
            LTRIM(RTRIM(
                CONCAT(
                    COALESCE(NULLIF(LTRIM(RTRIM(SUS.US_DDD)), ''), ''),
                    COALESCE(NULLIF(LTRIM(RTRIM(SUS.US_TEL)), ''), '')
                )
            ))
        ELSE NULL
    END AS cliente_telefone,
    CASE
        WHEN NULLIF(LTRIM(RTRIM(SUS.US_COD)), '') IS NOT NULL
         AND NULLIF(LTRIM(RTRIM(A1.A1_COD)), '') IS NULL THEN SUS.US_EMAIL
        ELSE NULL
    END AS cliente_email,
    CASE
        WHEN NULLIF(LTRIM(RTRIM(A1.A1_COD)), '') IS NOT NULL THEN 'cliente'
        WHEN NULLIF(LTRIM(RTRIM(SUS.US_COD)), '') IS NOT NULL THEN 'prospect'
        ELSE NULL
    END AS cliente_tipo_cadastro,
    U5.U5_CONTAT AS contato_nome,
    U5.U5_EMAIL AS contato_email,
    U5.U5_FONE AS contato_telefone,
    QB.QB_DESCRIC AS contato_departamento,
    E4.E4_DESCRI AS condicao_descricao,
    A3.A3_NOME AS vendedor_nome,
    A3.A3_EMAIL AS vendedor_email,
    A3.A3_TEL AS vendedor_telefone,
    UM.UM_DESC AS vendedor_cargo,
    CO.M0_NOMECOM AS empresa_nome,
    CO.M0_CGC AS empresa_cnpj,
    CO.M0_INSC AS empresa_inscricao_estadual,
    CO.M0_ENDENT AS empresa_endereco,
    CO.M0_BAIRENT AS empresa_bairro,
    CO.M0_CIDENT AS empresa_cidade,
    CO.M0_ESTENT AS empresa_uf,
    CO.M0_CEPENT AS empresa_cep,
    CO.M0_TEL AS empresa_telefone,
    (
        SELECT SUM(ADZ.ADZ_TOTAL)
        FROM ADZ010 ADZ WITH (NOLOCK)
        WHERE ADZ.D_E_L_E_T_ <> '*'
          AND ADZ.ADZ_PROPOS = ADY.ADY_PROPOS
          AND ADZ.ADZ_REVISA = ADY.ADY_PREVIS
    ) AS soma_valores_r_mil
{_COMMON_JOINS}
WHERE ADY.D_E_L_E_T_ <> '*'
  AND ADY.ADY_STATUS = 'A'
  AND ADY.ADY_PROPOS = ?
"""

DETAIL_ITEMS_SQL = """
SELECT
    ADZ.ADZ_ITEM AS item,
    ADZ.ADZ_PRODUT AS produto,
    COALESCE(NULLIF(RTRIM(ADZ.ADZ_DESCRI), ''), B1.B1_DESC) AS descricao,
    B1.B1_REFEREN AS referencia_cliente,
    B1.B1_POSIPI AS ncm,
    ADZ.ADZ_QTDVEN AS quantidade,
    ADZ.ADZ_UM AS unidade,
    ADZ.ADZ_PRCVEN AS preco_unitario,
    ADZ.ADZ_PRCVEN AS valor_bruto_r_mil,
    ADZ.ADZ_TOTAL AS valor_total,
    ADZ.ADZ_PRAZO AS prazo_dias,
    ADZ.ADZ_LTEMIN AS lote_minimo,
    SZ8_PRECO.Z8_ID AS id_formacao_preco,
    ICMS.aliquota_icms,
    PISCOFINS.aliquota_pis_cofins
FROM ADZ010 ADZ WITH (NOLOCK)
INNER JOIN ADY010 ADY WITH (NOLOCK)
  ON ADY.D_E_L_E_T_ <> '*'
 AND ADY.ADY_PROPOS = ADZ.ADZ_PROPOS
 AND ADY.ADY_PREVIS = ADZ.ADZ_REVISA
 AND ADY.ADY_STATUS = 'A'
LEFT JOIN SB1010 B1 WITH (NOLOCK)
  ON B1.D_E_L_E_T_ <> '*'
 AND B1.B1_COD = ADZ.ADZ_PRODUT
OUTER APPLY (
    SELECT TOP 1
        SZ8.R_E_C_N_O_ AS sz8_recno,
        SZ8.Z8_ID,
        SZ8.Z8_NROPOR,
        SZ8.Z8_COD,
        SZ8.Z8_DTEMISS,
        SZ8.Z8_PVSUGER,
        SZ8.Z8_MARGEM,
        SZ8.Z8_SITUA
    FROM dbo.SZ8010 SZ8 WITH (NOLOCK)
    WHERE ISNULL(SZ8.D_E_L_E_T_, '') <> '*'
      AND LTRIM(RTRIM(SZ8.Z8_NROPOR)) = LTRIM(RTRIM(ADY.ADY_OPORTU))
      AND LTRIM(RTRIM(SZ8.Z8_COD)) = LTRIM(RTRIM(ADZ.ADZ_PRODUT))
    ORDER BY
        SZ8.Z8_DTEMISS DESC,
        SZ8.R_E_C_N_O_ DESC
) SZ8_PRECO
OUTER APPLY (
    SELECT TOP 1
        SZ9.Z9_ALIQ AS aliquota_icms
    FROM dbo.SZ9010 SZ9 WITH (NOLOCK)
    WHERE ISNULL(SZ9.D_E_L_E_T_, '') <> '*'
      AND LTRIM(RTRIM(SZ9.Z9_IDZ8)) = LTRIM(RTRIM(SZ8_PRECO.Z8_ID))
      AND SZ9.Z9_IDFLD LIKE '3IMP%'
      AND UPPER(SZ9.Z9_DESC) LIKE '%ICMS%'
    ORDER BY
        SZ9.Z9_ITEM,
        SZ9.R_E_C_N_O_
) ICMS
OUTER APPLY (
    SELECT TOP 1
        SZ9.Z9_ALIQ AS aliquota_pis_cofins
    FROM dbo.SZ9010 SZ9 WITH (NOLOCK)
    WHERE ISNULL(SZ9.D_E_L_E_T_, '') <> '*'
      AND LTRIM(RTRIM(SZ9.Z9_IDZ8)) = LTRIM(RTRIM(SZ8_PRECO.Z8_ID))
      AND SZ9.Z9_IDFLD LIKE '3IMP%'
      AND (
          UPPER(SZ9.Z9_DESC) LIKE '%PIS%'
          OR UPPER(SZ9.Z9_DESC) LIKE '%COFINS%'
      )
    ORDER BY
        SZ9.Z9_ITEM,
        SZ9.R_E_C_N_O_
) PISCOFINS
WHERE ADZ.D_E_L_E_T_ <> '*'
  AND ADZ.ADZ_PROPOS = ?
ORDER BY ADZ.ADZ_ITEM
"""
