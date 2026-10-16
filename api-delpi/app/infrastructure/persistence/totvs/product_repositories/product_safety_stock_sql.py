"""SQL — estoque de segurança geral do produto (SB1010 × SBZ010) por filial.

Leitura cadastral canônica de produto: aplica a qualquer ``B1_TIPO``.
A especialização MP permanece exclusiva das queries de Suprimentos em
``supplies_repositories/safety_stock_sql.py`` — aqui não há filtro de tipo.

Regras de fonte compartilhadas com o read especializado:
- ``SBZ010.BZ_ESTSEG`` é o estoque de segurança por filial;
- ``RTRIM(SBZ.BZ_FILIAL) = ''`` não representa filial (linha sem branch) —
  excluída, mesma regra do read de Suprimentos;
- produto sem linha SBZ na filial retorna ``safety_stock`` NULL e
  ``sbz_rows = 0`` — ausência de registro, não zero.
"""

from __future__ import annotations


def product_safety_stock_sql(code: str, branches: tuple[str, ...]) -> tuple[str, tuple]:
    """Uma linha por filial do escopo com registro SBZ ativo; sem SBZ → NULLs.

    ``branches`` é sempre concreto (``01``/``02``) — o use case resolve o
    escopo autorizado antes de chamar. Parâmetros posicionais: branches (IN
    do LEFT JOIN) depois code (WHERE).
    """
    placeholders = ", ".join("?" for _ in branches)
    sql = f"""
        SELECT
            LTRIM(RTRIM(SB1.B1_COD))    AS product_code,
            LTRIM(RTRIM(SB1.B1_DESC))   AS description,
            LTRIM(RTRIM(SB1.B1_TIPO))   AS product_type,
            LTRIM(RTRIM(SB1.B1_UM))     AS unit,
            LTRIM(RTRIM(SB1.B1_MSBLQL)) AS blocked_flag,
            LTRIM(RTRIM(SBZ.BZ_FILIAL)) AS branch,
            COUNT(SBZ.BZ_COD)           AS sbz_rows,
            SUM(CAST(SBZ.BZ_ESTSEG AS FLOAT)) AS safety_stock
        FROM SB1010 SB1 WITH (NOLOCK)
        LEFT JOIN SBZ010 SBZ WITH (NOLOCK)
            ON LTRIM(RTRIM(SBZ.BZ_COD)) = LTRIM(RTRIM(SB1.B1_COD))
            AND SBZ.D_E_L_E_T_ = ''
            AND LTRIM(RTRIM(SBZ.BZ_FILIAL)) <> ''
            AND LTRIM(RTRIM(SBZ.BZ_FILIAL)) IN ({placeholders})
        WHERE SB1.D_E_L_E_T_ = ''
          AND LTRIM(RTRIM(SB1.B1_COD)) = ?
        GROUP BY
            SB1.B1_COD,
            SB1.B1_DESC,
            SB1.B1_TIPO,
            SB1.B1_UM,
            SB1.B1_MSBLQL,
            SBZ.BZ_FILIAL
        ORDER BY LTRIM(RTRIM(SBZ.BZ_FILIAL))
    """
    return sql, (*branches, code)
