"""Fragmentos SQL compartilhados do denominador de produção PPM."""

# Cruzamento OP apontada × ordem de produção (SC2010).
SC2_OP_JOIN = """
    LEFT JOIN SC2010 SC2
        ON SC2.D_E_L_E_T_ = ' '
       AND SC2.C2_FILIAL = SH6.H6_FILIAL
       AND SC2.C2_PRODUTO = SH6.H6_PRODUTO
       AND (
            SC2.C2_OP = SH6.H6_OP
            OR SC2.C2_NUM + SC2.C2_ITEM + SC2.C2_SEQUEN = SH6.H6_OP
       )
"""

# programado − max(0, programado − apontado) = apontado (limitado ao programado).
# apontado = MAX(H6_QTDPROD) por OP/operação final; programado = C2_QUANT.
QTD_PRODUZIDA_OP_EXPR = """
    CASE
        WHEN MAX(ISNULL(SC2.C2_QUANT, 0)) <= 0 THEN MAX(ISNULL(SH6.H6_QTDPROD, 0))
        ELSE MAX(ISNULL(SC2.C2_QUANT, 0)) - CASE
            WHEN MAX(ISNULL(SC2.C2_QUANT, 0)) > MAX(ISNULL(SH6.H6_QTDPROD, 0))
            THEN MAX(ISNULL(SC2.C2_QUANT, 0)) - MAX(ISNULL(SH6.H6_QTDPROD, 0))
            ELSE 0
        END
    END
"""
