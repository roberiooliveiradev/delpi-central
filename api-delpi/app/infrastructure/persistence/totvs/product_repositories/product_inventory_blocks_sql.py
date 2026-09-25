"""SQL — bloqueio de inventário SB2 (B2_DTINV / B2_DINVFIM) por filial, armazém e códigos."""

from __future__ import annotations


def inventory_blocks_sql(*, product_count: int) -> str:
    """Uma linha por produto com saldo SB2 no armazém informado.

    Produto sem SB2 não aparece: o consumidor trata ausência como sem bloqueio.
    """
    if product_count <= 0:
        raise ValueError("product_count deve ser positivo.")

    placeholders = ", ".join("?" * product_count)
    return f"""
        SELECT
            LTRIM(RTRIM(SB2.B2_COD)) AS product_code,
            LTRIM(RTRIM(SB2.B2_FILIAL)) AS branch,
            LTRIM(RTRIM(SB2.B2_LOCAL)) AS warehouse,
            LTRIM(RTRIM(ISNULL(SB2.B2_DTINV, ''))) AS inventory_block_start,
            LTRIM(RTRIM(ISNULL(SB2.B2_DINVFIM, ''))) AS inventory_block_end
        FROM SB2010 SB2 WITH (NOLOCK)
        WHERE SB2.D_E_L_E_T_ = ''
          AND LTRIM(RTRIM(SB2.B2_FILIAL)) = ?
          AND LTRIM(RTRIM(SB2.B2_LOCAL)) = ?
          AND LTRIM(RTRIM(SB2.B2_COD)) IN ({placeholders})
        ORDER BY LTRIM(RTRIM(SB2.B2_COD)) ASC
    """.strip()
