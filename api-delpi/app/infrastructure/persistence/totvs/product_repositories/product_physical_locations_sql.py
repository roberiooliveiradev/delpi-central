"""SQL — local físico de matéria-prima (SBZ010.BZ_MPLOCAL) por filial e códigos."""

from __future__ import annotations


def physical_locations_sql(*, product_count: int) -> str:
    """Uma linha por produto com indicador SBZ na filial.

    Produto sem SBZ não aparece: o consumidor trata ausência como local vazio,
    sem inventar endereço.
    """
    if product_count <= 0:
        raise ValueError("product_count deve ser positivo.")

    placeholders = ", ".join("?" * product_count)
    return f"""
        SELECT
            LTRIM(RTRIM(SBZ.BZ_COD)) AS product_code,
            LTRIM(RTRIM(ISNULL(SBZ.BZ_MPLOCAL, ''))) AS physical_location
        FROM SBZ010 SBZ WITH (NOLOCK)
        WHERE SBZ.D_E_L_E_T_ = ''
          AND LTRIM(RTRIM(SBZ.BZ_FILIAL)) = ?
          AND LTRIM(RTRIM(SBZ.BZ_COD)) IN ({placeholders})
        ORDER BY LTRIM(RTRIM(SBZ.BZ_COD)) ASC
    """.strip()
