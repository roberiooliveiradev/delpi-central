"""Fragmentos SQL do denominador PPM — apontamento no CT de inspeção final."""

# Tipos de produto incluídos no total produzido (PA + PI).
PPM_PRODUCED_B1_TIPOS = ("PA", "PI")

# Filtro dinâmico de CT de inspeção final (SHB010) — playbook expedição / produção.
CT_INSPECAO_NOME_LIKE = "%INSPE%FINAL%"

CT_INSPECAO_FINAL_CTE = """
    ct_inspecao_final AS (
        SELECT
            HB.HB_FILIAL,
            HB.HB_COD AS ct_inspecao,
            HB.HB_NOME AS nome_ct_inspecao
        FROM SHB010 HB
        WHERE
            HB.D_E_L_E_T_ = ' '
            AND UPPER(HB.HB_NOME) LIKE '%INSPE%FINAL%'
            {ct_branch_filter}
    )
"""

# Recurso apontado → centro de trabalho (SH1010).
SH1_RECURSO_JOIN = """
    INNER JOIN SH1010 SH1
        ON SH1.H1_FILIAL = SH6.H6_FILIAL
       AND SH1.H1_CODIGO = SH6.H6_RECURSO
       AND SH1.D_E_L_E_T_ = ' '
"""

CT_INSPECAO_JOIN = """
    INNER JOIN ct_inspecao_final CIF
        ON CIF.HB_FILIAL = SH6.H6_FILIAL
       AND CIF.ct_inspecao = SH1.H1_CTRAB
"""

# Soma H6_QTDPROD por OP/produto/operação no CT de inspeção (playbook).
QTD_PRODUZIDA_OP_EXPR = "SUM(CAST(SH6.H6_QTDPROD AS FLOAT))"

APONT_INSPECAO_CTE = """
    apont_inspecao AS (
        SELECT
            SH6.H6_FILIAL,
            SH6.H6_OP,
            SH6.H6_PRODUTO,
            SH6.H6_OPERAC,
            SB1.B1_TIPO,
            {qtd_expr} AS qtd_produzida_op
        FROM SH6010 SH6
        INNER JOIN SB1010 SB1
            ON SB1.B1_COD = SH6.H6_PRODUTO
           AND SB1.D_E_L_E_T_ = ' '
           AND SB1.B1_TIPO IN ('PA', 'PI')
        {sh1_join}
        {ct_join}
        WHERE
            SH6.D_E_L_E_T_ = ' '
            {sh6_branch_filter}
            AND SH6.H6_TIPO = 'P'
            AND SH6.H6_OP <> ''
            AND SH6.H6_PRODUTO <> ''
            AND SH6.H6_RECURSO <> ''
            {product_filter}
            AND SH6.H6_DTAPONT >= ?
            AND SH6.H6_DTAPONT < ?
        GROUP BY
            SH6.H6_FILIAL,
            SH6.H6_OP,
            SH6.H6_PRODUTO,
            SH6.H6_OPERAC,
            SB1.B1_TIPO
    )
"""
