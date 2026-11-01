"""SQL builders for the R09 billing × MOD breakdown (doc 141, DR-1/DR-2).

Every builder returns a parameterized ``SELECT`` — no caller value ever
reaches the SQL text. The three reads mirror the proven DLP204 chain:

1. ``billed_quantities_sql`` — the ``SD2010`` + ``F4_DUPLIC='S'`` billing
   population on the ``D2_EMISSAO`` axis. The literal WHERE of
   ``fGetProds`` does NOT filter ``D2_TIPO`` for anchor membership, so
   ``has_billing`` keeps every duplic-S line while ``billed_qty`` applies
   the ``D2_TIPO<>'D'`` sum proven for QTDFAT (doc 85 §9 BR-R09-003/006).
2. ``structure_edges_sql`` — direct ``SG1010`` children of a parent set
   (``Estrut`` semantics: own filial, current validity, no SGG — the
   historical call used ``lPreEstru=.F.``).
3. ``route_operations_sql`` — cadastral ``SG2010`` operations ranked like
   the canonical ``SG2_RANKED`` CTE (latest record per filial/produto/
   operação, branch-specific preferred over shared blank-filial), with
   the ``SH1010.H1_CCUSTO`` → ``SB1010 MOD*`` bridge proven in
   BR-R09-007.

The SHY frozen-OP route (BR-R09-008, ``HY_TEMPAD`` primary in ~96% of
artifact lines) is a documented gap of Slice 1: the SP's OP selection is
not reconstructible with evidence, so ``stdTime`` comes from the
cadastral route and the divergence is measured by the parity gate.
"""

from __future__ import annotations

from typing import Any

# MV_PAR09 default — operation route filter proven for the artifact run
# (doc 85 §9 BR-R09-002). Kept as a builder parameter so the constant is
# declared once, next to its evidence.
DEFAULT_ROUTE_CODE = "01"


def _in_placeholders(count: int) -> str:
    return ", ".join("?" for _ in range(count))


def billed_quantities_sql(*, branch: str) -> tuple[str, list[Any]]:
    """Per-product billed qty for one branch on the ``D2_EMISSAO`` axis."""
    sql = """
SELECT RTRIM(D2.D2_COD) AS product_code,
       1 AS has_billing,
       CAST(SUM(CASE WHEN RTRIM(D2.D2_TIPO) <> 'D'
                     THEN D2.D2_QUANT ELSE 0 END) AS FLOAT) AS billed_qty
  FROM SD2010 D2 WITH (NOLOCK)
 WHERE D2.D_E_L_E_T_ = ' '
   AND D2.D2_FILIAL = ?
   AND D2.D2_EMISSAO BETWEEN ? AND ?
   AND EXISTS (
        SELECT 1
          FROM SF4010 SF4 WITH (NOLOCK)
         WHERE SF4.D_E_L_E_T_ = ' '
           AND SF4.F4_CODIGO = D2.D2_TES
           AND SF4.F4_DUPLIC = 'S')
 GROUP BY D2.D2_COD
"""
    return sql, [branch]


def billed_quantities_params(
    *, period_start: str, period_end: str, branch: str
) -> list[Any]:
    """Placeholder order of ``billed_quantities_sql``."""
    return [branch, period_start, period_end]


def structure_edges_sql(
    *, parent_codes: list[str], branch: str
) -> tuple[str, list[Any]]:
    """Direct SG1 children of ``parent_codes`` (``Estrut`` level-1 read).

    Replicates ``dbSeek(xFilial()+cProduto)``: exact branch filial only.
    Component validity (``G1_INI``/``G1_FIM``) is evaluated at execution
    date — the same runtime reference ``ExplEstr`` uses. The ``qty>0``
    and self-component guards stay in the use case (``Estrut`` skips
    ``cCodigo == cComponente`` and ``ExplEstr <= 0``).
    """
    if not parent_codes:
        raise ValueError("parent_codes deve conter pelo menos 1 código.")
    placeholders = _in_placeholders(len(parent_codes))
    sql = f"""
SELECT RTRIM(G1.G1_COD)  AS parent_code,
       RTRIM(G1.G1_COMP) AS component_code,
       RTRIM(G1.G1_TRT)  AS component_seq,
       CAST(G1.G1_QUANT AS FLOAT) AS quantity_per_unit
  FROM SG1010 G1 WITH (NOLOCK)
 WHERE G1.D_E_L_E_T_ = ' '
   AND G1.G1_FILIAL = ?
   AND G1.G1_COD IN ({placeholders})
   AND (G1.G1_INI = '' OR G1.G1_INI <= CONVERT(CHAR(8), GETDATE(), 112))
   AND (G1.G1_FIM = '' OR G1.G1_FIM >= CONVERT(CHAR(8), GETDATE(), 112))
 ORDER BY G1.G1_COD, G1.G1_TRT, G1.G1_COMP
"""
    return sql, [branch, *parent_codes]


def route_operations_sql(
    *, product_codes: list[str], branch: str, route_code: str = DEFAULT_ROUTE_CODE
) -> tuple[str, list[Any]]:
    """Cadastral SG2 operations + MOD bridge for ``product_codes``.

    Latest SG2 record per (produto, operação) — same ranking mold as the
    canonical ``SG2_RANKED`` CTE, with branch-specific filial preferred
    over the shared blank-filial row. ``SH1010`` bridges ``G2_RECURSO``
    to the cost center that mirrors the ``MOD*`` item code
    (``B1_COD = 'MOD' + H1_CCUSTO``, proven live: ``CT-33A`` → CC ``393``
    → ``MOD393``; doc 85 §9 BR-R09-007). The resource lookup is a TOP 1
    APPLY (branch-specific preferred) — a plain join would multiply the
    operation lines once per SH1 filial row.
    """
    if not product_codes:
        raise ValueError("product_codes deve conter pelo menos 1 código.")
    placeholders = _in_placeholders(len(product_codes))
    sql = f"""
WITH SG2_RANKED AS (
    SELECT
        RTRIM(G2.G2_PRODUTO) AS product_code,
        RTRIM(G2.G2_OPERAC)  AS operation,
        RTRIM(G2.G2_DESCRI)  AS operation_description,
        RTRIM(G2.G2_RECURSO) AS resource,
        TRY_CAST(REPLACE(LTRIM(RTRIM(G2.G2_TEMPAD)), ',', '.') AS FLOAT)
            AS std_time,
        RTRIM(G2.G2_FILIAL)  AS sg2_filial,
        ROW_NUMBER() OVER (
            PARTITION BY RTRIM(G2.G2_PRODUTO), RTRIM(G2.G2_OPERAC)
            ORDER BY
                CASE WHEN G2.G2_FILIAL = ? THEN 0 ELSE 1 END,
                G2.R_E_C_N_O_ DESC
        ) AS rn
    FROM SG2010 G2 WITH (NOLOCK)
    WHERE G2.D_E_L_E_T_ = ' '
      AND G2.G2_FILIAL IN ('', ?)
      AND RTRIM(G2.G2_CODIGO) = ?
      AND G2.G2_PRODUTO IN ({placeholders})
)
SELECT SG2.product_code,
       SG2.operation,
       SG2.operation_description,
       SG2.resource,
       SG2.std_time,
       RTRIM(MODP.B1_COD)   AS mod_item,
       RTRIM(MODP.B1_DESC)  AS mod_description,
       RTRIM(MODP.B1_UM)    AS mod_unit
  FROM SG2_RANKED SG2
  OUTER APPLY (
      SELECT TOP 1 RTRIM(SH1.H1_CCUSTO) AS ccusto
        FROM SH1010 SH1 WITH (NOLOCK)
       WHERE SH1.D_E_L_E_T_ = ' '
         AND SH1.H1_CODIGO = SG2.resource
         AND SH1.H1_FILIAL IN ('', ?)
       ORDER BY CASE WHEN SH1.H1_FILIAL = ? THEN 0 ELSE 1 END
  ) SH1
  LEFT JOIN SB1010 MODP WITH (NOLOCK)
         ON MODP.D_E_L_E_T_ = ' '
        AND MODP.B1_COD = 'MOD' + NULLIF(RTRIM(SH1.ccusto), '')
 WHERE SG2.rn = 1
 ORDER BY SG2.product_code, SG2.operation
"""
    return sql, [branch, branch, route_code, *product_codes, branch, branch]
