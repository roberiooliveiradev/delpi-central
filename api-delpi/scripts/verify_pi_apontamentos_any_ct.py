"""Verifica se OPs/PIs da planilha têm apontamento em qualquer CT."""
from app.infrastructure.persistence.totvs.ppm_repositories.ppm_query_repository import (
    PpmQueryRepository,
)

OPS = ["24250401001", "24250501001", "24184701001", "24250301001"]
PRODUCTS = ["50232465", "50233615", "50233616"]

SQL_ANY_CT = """
SELECT TOP 20
    LTRIM(RTRIM(SH6.H6_OP)) AS op,
    LTRIM(RTRIM(SH6.H6_PRODUTO)) AS product_code,
    LTRIM(RTRIM(SH1.H1_CTRAB)) AS ct,
    LTRIM(RTRIM(HB.HB_NOME)) AS ct_nome,
    SH6.H6_DTAPONT AS dt,
    CAST(SH6.H6_QTDPROD AS FLOAT) AS qtd_milheiro
FROM SH6010 SH6
LEFT JOIN SH1010 SH1
    ON SH1.H1_FILIAL = SH6.H6_FILIAL
   AND SH1.H1_CODIGO = SH6.H6_RECURSO
   AND SH1.D_E_L_E_T_ = ' '
LEFT JOIN SHB010 HB
    ON HB.HB_FILIAL = SH6.H6_FILIAL
   AND HB.HB_COD = SH1.H1_CTRAB
   AND HB.D_E_L_E_T_ = ' '
WHERE SH6.D_E_L_E_T_ = ' '
  AND SH6.H6_FILIAL = '01'
  AND SH6.H6_TIPO = 'P'
  AND SH6.H6_OP = ?
ORDER BY SH6.H6_DTAPONT
"""

SQL_PROD_SUM = """
SELECT
    LTRIM(RTRIM(SH1.H1_CTRAB)) AS ct,
    LTRIM(RTRIM(HB.HB_NOME)) AS ct_nome,
    SUM(CAST(SH6.H6_QTDPROD AS FLOAT)) * 1000 AS total_un,
    COUNT(*) AS apont_count
FROM SH6010 SH6
LEFT JOIN SH1010 SH1
    ON SH1.H1_FILIAL = SH6.H6_FILIAL
   AND SH1.H1_CODIGO = SH6.H6_RECURSO
   AND SH1.D_E_L_E_T_ = ' '
LEFT JOIN SHB010 HB
    ON HB.HB_FILIAL = SH6.H6_FILIAL
   AND HB.HB_COD = SH1.H1_CTRAB
   AND HB.D_E_L_E_T_ = ' '
WHERE SH6.D_E_L_E_T_ = ' '
  AND SH6.H6_FILIAL = '01'
  AND SH6.H6_TIPO = 'P'
  AND SH6.H6_PRODUTO = ?
  AND SH6.H6_DTAPONT >= '20260101'
  AND SH6.H6_DTAPONT < '20260401'
GROUP BY SH1.H1_CTRAB, HB.HB_NOME
ORDER BY total_un DESC
"""


def main() -> None:
    with PpmQueryRepository() as repo:
        print("=== Apontamentos por OP da planilha (qualquer CT) ===")
        for op in OPS:
            rows = repo.execute_query(SQL_ANY_CT, (op,)) or []
            print(f"\nOP {op}: {len(rows)} apontamento(s)")
            for row in rows[:8]:
                qtd = float(row.get("qtd_milheiro") or 0) * 1000
                print(
                    f"  prod={row.get('product_code')} ct={row.get('ct')} "
                    f"({row.get('ct_nome')}) dt={row.get('dt')} qtd={qtd:,.0f} un"
                )

        print("\n=== PIs jan-mar/2026 — apontamento por CT (qualquer) ===")
        for prod in PRODUCTS:
            rows = repo.execute_query(SQL_PROD_SUM, (prod,)) or []
            total = sum(float(r.get("total_un") or 0) for r in rows)
            print(f"\n{prod}: total apontado jan-mar = {total:,.0f} un em {len(rows)} CT(s)")
            for row in rows:
                print(
                    f"  ct={row.get('ct')} ({row.get('ct_nome')}): "
                    f"{float(row.get('total_un') or 0):,.0f} un ({row.get('apont_count')} apont.)"
                )


if __name__ == "__main__":
    main()
