"""Validação integrada: denominador PPM por CT de inspeção final (jan–mai/2026)."""
from types import SimpleNamespace

from app.infrastructure.persistence.totvs.ppm_repositories.ppm_query_repository import (
    PpmQueryRepository,
)

MONTHS = [
    ("2026-01-01", "2026-01-31", "Jan/2026"),
    ("2026-02-01", "2026-02-28", "Feb/2026"),
    ("2026-03-01", "2026-03-31", "Mar/2026"),
    ("2026-04-01", "2026-04-30", "Abr/2026"),
    ("2026-05-01", "2026-05-31", "Mai/2026"),
]

SQL_CTS = """
SELECT HB_FILIAL, HB_COD, HB_NOME
FROM SHB010
WHERE D_E_L_E_T_ = ' ' AND UPPER(HB_NOME) LIKE '%INSPE%FINAL%'
ORDER BY HB_FILIAL, HB_COD
"""

SQL_BY_TIPO = """
WITH ct_inspecao_final AS (
    SELECT HB.HB_FILIAL, HB.HB_COD AS ct_inspecao
    FROM SHB010 HB
    WHERE HB.D_E_L_E_T_ = ' ' AND UPPER(HB.HB_NOME) LIKE '%INSPE%FINAL%'
      AND HB.HB_FILIAL = ?
),
apont_inspecao AS (
    SELECT SB1.B1_TIPO, SUM(CAST(SH6.H6_QTDPROD AS FLOAT)) AS qtd_milheiro
    FROM SH6010 SH6
    INNER JOIN SB1010 SB1 ON SB1.B1_COD = SH6.H6_PRODUTO AND SB1.D_E_L_E_T_ = ' '
       AND SB1.B1_TIPO IN ('PA', 'PI')
    INNER JOIN SH1010 SH1 ON SH1.H1_FILIAL = SH6.H6_FILIAL AND SH1.H1_CODIGO = SH6.H6_RECURSO
       AND SH1.D_E_L_E_T_ = ' '
    INNER JOIN ct_inspecao_final CIF ON CIF.HB_FILIAL = SH6.H6_FILIAL AND CIF.ct_inspecao = SH1.H1_CTRAB
    WHERE SH6.D_E_L_E_T_ = ' ' AND SH6.H6_FILIAL = ? AND SH6.H6_TIPO = 'P'
      AND SH6.H6_OP <> '' AND SH6.H6_PRODUTO <> '' AND SH6.H6_RECURSO <> ''
      AND SH6.H6_DTAPONT >= ? AND SH6.H6_DTAPONT < ?
    GROUP BY SB1.B1_TIPO
)
SELECT B1_TIPO, qtd_milheiro * 1000 AS total_un FROM apont_inspecao
"""


def _exclusive_end(date_end: str) -> str:
    from datetime import datetime, timedelta

    parsed = datetime.strptime(date_end.replace("-", ""), "%Y%m%d")
    return (parsed + timedelta(days=1)).strftime("%Y%m%d")


def main() -> None:
    print("CTs de inspeção final (SHB010):")
    with PpmQueryRepository() as repo:
        for row in repo.execute_query(SQL_CTS, ()) or []:
            print(f"  filial {row.get('HB_FILIAL')} | {row.get('HB_COD')} | {row.get('HB_NOME')}")

    print("\nFilial 01 — PPM get_summary (PA + PI, CT inspeção)")
    print("=" * 58)
    print(f"{'Mês':<12} {'Total (un)':>14} {'PA':>12} {'PI':>12}")
    print("-" * 58)

    acum = 0.0
    for start, end, label in MONTHS:
            ini = start.replace("-", "")
            fim_ex = _exclusive_end(end)
            req = SimpleNamespace(
                type="internal",
                branch="01",
                date_start=start,
                date_end=end,
            )
            with PpmQueryRepository() as repo:
                tipos = {
                    str(r.get("B1_TIPO") or "").strip(): float(r.get("total_un") or 0)
                    for r in repo.execute_query(SQL_BY_TIPO, ("01", "01", ini, fim_ex)) or []
                }
            with PpmQueryRepository() as repo:
                summary = repo.get_summary(req)
            total = summary.total_produzido_un
            acum += total
            print(
                f"{label:<12} {total:>14,.0f} {tipos.get('PA', 0):>12,.0f} "
                f"{tipos.get('PI', 0):>12,.0f}"
            )

    print("-" * 58)
    print(f"{'Acumulado':<12} {acum:>14,.0f}")


if __name__ == "__main__":
    main()
