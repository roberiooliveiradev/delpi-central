"""SQL — tempo padrão de uma única operação de OP (SC2 + SHY010 + SG2010).

Consulta focada por ``branch + production_order + operation_code``: traz no
máximo uma linha, sem varrer a filial inteira. Os campos SHY/SG2 saem crus —
a prioridade canônica (TEMPAD → TEMPOM/QUANT → G2_TEMPAD) e a normalização
para segundos por peça ficam no domínio
(``app/domain/production/production_standard_time.py``), mesma regra do SQL
``FABRIL_UNIT_HOURS_SQL`` usado pela eficiência fabril.

Comparações diretas (sem LTRIM/RTRIM no WHERE): SQL Server ignora espaços à
direita em campos CHAR, o que preserva o seek pelos índices de OP/produto.
"""

from __future__ import annotations

_SHY_NUMERIC = {
    "hy_tempad": "SHY.HY_TEMPAD",
    "hy_tempom": "SHY.HY_TEMPOM",
    "hy_quant": "SHY.HY_QUANT",
    "hy_setup": "SHY.HY_SETUP",
}
_SG2_NUMERIC = {
    "g2_tempad": "SG2.G2_TEMPAD",
    "g2_setup": "SG2.G2_SETUP",
}


def _numeric_expr(column: str) -> str:
    return f"TRY_CAST(REPLACE(LTRIM(RTRIM({column})), ',', '.') AS FLOAT)"


def build_operation_standard_time_query() -> str:
    """Query da operação única.

    Ordem dos placeholders: SHY (filial, OP, operação), SG2 (filial,
    operação), SC2 (filial, OP).
    """
    shy_columns = ",\n            ".join(
        f"{_numeric_expr(col)} AS {alias}" for alias, col in _SHY_NUMERIC.items()
    )
    sg2_columns = ",\n            ".join(
        f"{_numeric_expr(col)} AS {alias}" for alias, col in _SG2_NUMERIC.items()
    )
    query = f"""
SELECT
    RTRIM(LTRIM(OP.C2_FILIAL))            AS branch,
    RTRIM(LTRIM(OP.C2_OP))                AS production_order,
    RTRIM(LTRIM(OP.C2_PRODUTO))           AS product_code,
    RTRIM(LTRIM(ISNULL(OP.C2_UM, '')))    AS unit,
    SHY.hy_tempad,
    SHY.hy_tempom,
    SHY.hy_quant,
    SHY.hy_setup,
    SG2.g2_tempad,
    SG2.g2_setup,
    CASE
        WHEN SHY.has_row = 1 OR SG2.has_row = 1 THEN 1
        ELSE 0
    END AS operation_exists
FROM SC2010 OP WITH (NOLOCK)
OUTER APPLY (
    SELECT TOP 1
            {shy_columns},
            1 AS has_row
    FROM SHY010 SHY WITH (NOLOCK)
    WHERE SHY.D_E_L_E_T_ = ''
      AND SHY.HY_FILIAL = ?
      AND SHY.HY_OP = ?
      AND SHY.HY_OPERAC = ?
    ORDER BY SHY.R_E_C_N_O_ DESC
) SHY
OUTER APPLY (
    SELECT TOP 1
            {sg2_columns},
            1 AS has_row
    FROM SG2010 SG2 WITH (NOLOCK)
    WHERE SG2.D_E_L_E_T_ = ''
      AND SG2.G2_FILIAL = ?
      AND SG2.G2_PRODUTO = OP.C2_PRODUTO
      AND SG2.G2_CODIGO = OP.C2_ROTEIRO
      AND SG2.G2_OPERAC = ?
    ORDER BY SG2.R_E_C_N_O_ DESC
) SG2
WHERE OP.D_E_L_E_T_ = ''
  AND OP.C2_FILIAL = ?
  AND OP.C2_OP = ?
"""
    return query
