"""CTEs/joins set-based SHY + SG2 (tempo padrão) — compartilhado OEE e eficiência fabril."""

from __future__ import annotations

from app.domain.production.production_fabril_appointment_scope import (
    DEFAULT_PRODUCTION_BRANCHES,
)
from app.domain.services.supplies.safety_stock_stock_projection_service import (
    FINISHED_PRODUCTION_ORDER_SUFFIX,
)


def _branch_filter_sql(
    *,
    column_sql: str,
    branch: str | None,
    branches: tuple[str, ...],
) -> tuple[str, list]:
    params: list = []
    if branch:
        return f"AND {column_sql} = ?", [branch]
    placeholders = ", ".join("?" for _ in branches)
    params.extend(branches)
    return f"AND {column_sql} IN ({placeholders})", params


def build_fabril_standard_time_ranked_ctes(
    *,
    branch: str | None,
    branches: tuple[str, ...] = DEFAULT_PRODUCTION_BRANCHES,
) -> tuple[str, tuple]:
    """CTEs ``SHY_RANKED`` + ``SG2_RANKED`` (ritmo unitário / setup / fallback G2)."""
    params: list = []
    shy_branch_filter, shy_params = _branch_filter_sql(
        column_sql="RTRIM(LTRIM(SHY.HY_FILIAL))",
        branch=branch,
        branches=branches,
    )
    params.extend(shy_params)
    sg2_branch_filter, sg2_params = _branch_filter_sql(
        column_sql="RTRIM(LTRIM(SG2.G2_FILIAL))",
        branch=branch,
        branches=branches,
    )
    params.extend(sg2_params)

    cte = f"""
SHY_RANKED AS (
    SELECT
        RTRIM(LTRIM(SHY.HY_FILIAL)) AS match_filial,
        RTRIM(LTRIM(SHY.HY_OP)) AS match_op,
        RTRIM(LTRIM(SHY.HY_OPERAC)) AS match_operacao,
        TRY_CAST(REPLACE(LTRIM(RTRIM(SHY.HY_TEMPOM)), ',', '.') AS FLOAT) AS HY_TEMPOM,
        TRY_CAST(REPLACE(LTRIM(RTRIM(SHY.HY_TEMPAD)), ',', '.') AS FLOAT) AS HY_TEMPAD,
        TRY_CAST(REPLACE(LTRIM(RTRIM(SHY.HY_QUANT)), ',', '.') AS FLOAT) AS HY_QUANT,
        TRY_CAST(REPLACE(LTRIM(RTRIM(SHY.HY_SETUP)), ',', '.') AS FLOAT) AS HY_SETUP,
        ROW_NUMBER() OVER (
            PARTITION BY
                RTRIM(LTRIM(SHY.HY_FILIAL)),
                RTRIM(LTRIM(SHY.HY_OP)),
                RTRIM(LTRIM(SHY.HY_OPERAC))
            ORDER BY SHY.R_E_C_N_O_ DESC
        ) AS rn
    FROM SHY010 SHY WITH (NOLOCK)
    WHERE SHY.D_E_L_E_T_ = ''
      {shy_branch_filter}
),
SG2_RANKED AS (
    SELECT
        RTRIM(LTRIM(SG2.G2_FILIAL)) AS match_filial,
        RTRIM(LTRIM(SG2.G2_PRODUTO)) AS match_produto,
        RTRIM(LTRIM(SG2.G2_OPERAC)) AS match_operacao,
        RTRIM(LTRIM(SG2.G2_DESCRI)) AS DESCRICAO_OPERACAO,
        TRY_CAST(REPLACE(LTRIM(RTRIM(SG2.G2_TEMPAD)), ',', '.') AS FLOAT) AS G2_TEMPAD,
        TRY_CAST(REPLACE(LTRIM(RTRIM(SG2.G2_SETUP)), ',', '.') AS FLOAT) AS G2_SETUP,
        ROW_NUMBER() OVER (
            PARTITION BY
                RTRIM(LTRIM(SG2.G2_FILIAL)),
                RTRIM(LTRIM(SG2.G2_PRODUTO)),
                RTRIM(LTRIM(SG2.G2_OPERAC))
            ORDER BY SG2.R_E_C_N_O_ DESC
        ) AS rn
    FROM SG2010 SG2 WITH (NOLOCK)
    WHERE SG2.D_E_L_E_T_ = ''
      {sg2_branch_filter}
)"""
    return cte, tuple(params)


def build_fabril_pa_ranked_cte(
    *,
    branch: str | None,
    branches: tuple[str, ...] = DEFAULT_PRODUCTION_BRANCHES,
) -> tuple[str, tuple]:
    """CTE ``PA_RANKED`` (produto acabado via OP mãe SC2)."""
    pa_branch_filter, pa_params = _branch_filter_sql(
        column_sql="RTRIM(LTRIM(FP.C2_FILIAL))",
        branch=branch,
        branches=branches,
    )
    cte = f"""
PA_RANKED AS (
    SELECT
        RTRIM(LTRIM(FP.C2_FILIAL)) AS match_filial,
        RTRIM(LTRIM(FP.C2_OP)) AS match_finished_op,
        RTRIM(LTRIM(FP.C2_PRODUTO)) AS PRODUTO_ACABADO,
        ROW_NUMBER() OVER (
            PARTITION BY
                RTRIM(LTRIM(FP.C2_FILIAL)),
                RTRIM(LTRIM(FP.C2_OP))
            ORDER BY FP.R_E_C_N_O_ DESC
        ) AS rn
    FROM SC2010 FP WITH (NOLOCK)
    WHERE FP.D_E_L_E_T_ = ''
      AND RIGHT(RTRIM(LTRIM(FP.C2_OP)), 5) = '{FINISHED_PRODUCTION_ORDER_SUFFIX}'
      {pa_branch_filter}
)"""
    return cte, tuple(pa_params)


def build_fabril_pa_and_operation_ranked_ctes(
    *,
    branch: str | None,
    branches: tuple[str, ...] = DEFAULT_PRODUCTION_BRANCHES,
) -> tuple[str, tuple]:
    """CTEs set-based: PA (SC2 mãe) + tempo padrão OP (SHY) + roteiro (SG2)."""
    pa_cte, pa_params = build_fabril_pa_ranked_cte(branch=branch, branches=branches)
    std_cte, std_params = build_fabril_standard_time_ranked_ctes(
        branch=branch,
        branches=branches,
    )
    # Remove leading newline duplication between CTEs.
    combined = f"{pa_cte.rstrip()},\n{std_cte.lstrip()}"
    return combined, pa_params + std_params


FABRIL_STANDARD_TIME_JOINS = """
LEFT JOIN SHY_RANKED SHY
    ON SHY.rn = 1
   AND SHY.match_filial = RTRIM(LTRIM(EF.FILIAL))
   AND SHY.match_op = RTRIM(LTRIM(EF.OP))
   AND SHY.match_operacao = RTRIM(LTRIM(EF.OPERACAO))
LEFT JOIN SG2_RANKED SG2
    ON SG2.rn = 1
   AND SG2.match_filial = RTRIM(LTRIM(EF.FILIAL))
   AND SG2.match_produto = RTRIM(LTRIM(EF.PRODUTO))
   AND SG2.match_operacao = RTRIM(LTRIM(EF.OPERACAO))
"""

_FINISHED_OP_FROM_EF = (
    f"LEFT(RTRIM(EF.OP), 6) + '{FINISHED_PRODUCTION_ORDER_SUFFIX}'"
)

FABRIL_PA_AND_STANDARD_TIME_JOINS = f"""
LEFT JOIN PA_RANKED FP
    ON FP.rn = 1
   AND FP.match_filial = RTRIM(LTRIM(EF.FILIAL))
   AND LEN(RTRIM(EF.OP)) >= 6
   AND FP.match_finished_op = {_FINISHED_OP_FROM_EF}
{FABRIL_STANDARD_TIME_JOINS}
"""
