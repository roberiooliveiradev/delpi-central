"""Validação integrada: regra programado − saldo = apontado vs MAX puro (jan–mai/2026)."""
from dataclasses import dataclass

from app.domain.services.ppm_produced_quantity import resolve_produced_quantity_milheiro
from app.infrastructure.persistence.totvs.ppm_repositories.ppm_production_sql import (
    QTD_PRODUZIDA_OP_EXPR,
    SC2_OP_JOIN,
)
from app.infrastructure.persistence.totvs.ppm_repositories.ppm_query_repository import (
    PpmQueryRepository,
)

MONTHS = [
    ("20260101", "20260201", "Jan/2026"),
    ("20260201", "20260301", "Fev/2026"),
    ("20260301", "20260401", "Mar/2026"),
    ("20260401", "20260501", "Abr/2026"),
    ("20260501", "20260601", "Mai/2026"),
]

SQL_COMPARE = f"""
WITH roteiro_final AS (
  SELECT G2.G2_FILIAL, G2.G2_PRODUTO, MAX(G2.G2_OPERAC) AS operacao_final
  FROM SG2010 G2
  WHERE G2.D_E_L_E_T_ = ' ' AND G2.G2_FILIAL = '01'
    AND (G2.G2_DTINI = '' OR G2.G2_DTINI < ?)
    AND (G2.G2_DTFIM = '' OR G2.G2_DTFIM >= ?)
  GROUP BY G2.G2_FILIAL, G2.G2_PRODUTO
),
base AS (
  SELECT
    MAX(CAST(SC2.C2_QUANT AS FLOAT)) AS programado,
    MAX(CAST(SH6.H6_QTDPROD AS FLOAT)) AS apontado_max,
    {QTD_PRODUZIDA_OP_EXPR.strip()} AS qtd_nova_regra
  FROM SH6010 SH6
  INNER JOIN roteiro_final RF
    ON RF.G2_FILIAL = SH6.H6_FILIAL AND RF.G2_PRODUTO = SH6.H6_PRODUTO
   AND RF.operacao_final = SH6.H6_OPERAC
  INNER JOIN SB1010 SB1 ON SB1.B1_COD = SH6.H6_PRODUTO AND SB1.B1_TIPO = 'PA' AND SB1.D_E_L_E_T_ = ' '
  {SC2_OP_JOIN}
  WHERE SH6.D_E_L_E_T_ = ' ' AND SH6.H6_FILIAL = '01' AND SH6.H6_TIPO = 'P'
    AND SH6.H6_OP <> '' AND SH6.H6_PRODUTO <> ''
    AND SH6.H6_DTAPONT >= ? AND SH6.H6_DTAPONT < ?
  GROUP BY SH6.H6_FILIAL, SH6.H6_OP, SH6.H6_PRODUTO, SH6.H6_OPERAC
)
SELECT
  SUM(apontado_max) * 1000 AS total_max_puro,
  SUM(qtd_nova_regra) * 1000 AS total_nova_regra,
  SUM(CASE WHEN apontado_max > programado AND programado > 0 THEN 1 ELSE 0 END) AS ops_apont_acima_prog,
  SUM(CASE WHEN qtd_nova_regra <> apontado_max THEN 1 ELSE 0 END) AS ops_regra_diferente_max
FROM base
"""


@dataclass
class MonthResult:
    label: str
    total_max: float
    total_nova: float
    ops_acima: int
    ops_diff: int


def main() -> None:
    results: list[MonthResult] = []

    with PpmQueryRepository() as repo:
        for ini, fim, label in MONTHS:
            row = repo.execute_one(SQL_COMPARE, (fim, ini, ini, fim)) or {}
            results.append(
                MonthResult(
                    label=label,
                    total_max=float(row.get("total_max_puro") or 0),
                    total_nova=float(row.get("total_nova_regra") or 0),
                    ops_acima=int(row.get("ops_apont_acima_prog") or 0),
                    ops_diff=int(row.get("ops_regra_diferente_max") or 0),
                )
            )

    print("Validação filial 01 — MAX puro vs programado − saldo = apontado")
    print("=" * 72)
    print(f"{'Mês':<12} {'MAX puro':>12} {'Nova regra':>12} {'Δ':>8} {'OPs>prog':>10}")
    print("-" * 72)
    for r in results:
        delta = r.total_nova - r.total_max
        print(
            f"{r.label:<12} {r.total_max:>12,.0f} {r.total_nova:>12,.0f} "
            f"{delta:>+8,.0f} {r.ops_acima:>10}"
        )

    acum_max = sum(r.total_max for r in results)
    acum_nova = sum(r.total_nova for r in results)
    print("-" * 72)
    print(f"{'Acumulado':<12} {acum_max:>12,.0f} {acum_nova:>12,.0f} {acum_nova - acum_max:>+8,.0f}")

    # amostra Python vs SQL
    sample = resolve_produced_quantity_milheiro(programado=1.0, apontado_max=1.2)
    assert sample == 1.0
    print()
    print("OK: função Python coerente com limite ao programado (1.0 vs apont 1.2 → 1.0)")
    if acum_max == acum_nova:
        print("OK: jan–mai/2026 — nova regra idêntica ao MAX (nenhuma OP acima do programado no impacto agregado)")
    else:
        print(f"INFO: diferença agregada {acum_nova - acum_max:+,.0f} un.")


if __name__ == "__main__":
    main()
