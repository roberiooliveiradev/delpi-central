"""Lookup SB1 para valoração gerencial de movimentos de inventário.

Uma linha de SB1 por movimento, priorizando cadastro da filial e depois
cadastro global. OUTER APPLY (0..1) evita multiplicar quantidades ou valores
caso existam registros de produto para mais de uma filial.
"""

from __future__ import annotations


def inventory_adjustment_product_apply(
    *, movement_alias: str = "SD3", code_field: str = "D3_COD",
    branch_field: str = "D3_FILIAL",
) -> str:
    """Anexa SB1V para identificar B1_TPMAT e fornecer descrição/UM.

    Os aliases/nomes de coluna são exclusivamente literais internos, nunca
    provenientes de filtros enviados pelo usuário.
    """
    code = f"{movement_alias}.{code_field}"
    branch = f"{movement_alias}.{branch_field}"
    return f"""
        OUTER APPLY (
            SELECT TOP (1)
                SB1.B1_TPMAT,
                SB1.B1_DESC,
                SB1.B1_UM
            FROM SB1010 SB1 WITH (NOLOCK)
            WHERE SB1.D_E_L_E_T_ = ''
              AND SB1.B1_COD = {code}
              AND (
                  SB1.B1_FILIAL = {branch}
                  OR SB1.B1_FILIAL = ''
                  OR SB1.B1_FILIAL IS NULL
              )
            ORDER BY
                CASE WHEN SB1.B1_FILIAL = {branch} THEN 0 ELSE 1 END,
                SB1.R_E_C_N_O_ DESC
        ) SB1V
    """
