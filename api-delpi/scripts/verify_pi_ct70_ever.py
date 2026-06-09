"""Verifica se PIs 50232xxx/50233xxx já apontaram no CT-70 (inspeção final)."""
from app.infrastructure.persistence.totvs.ppm_repositories.ppm_query_repository import (
    PpmQueryRepository,
)

PRODUCTS = ("50232465", "50233615", "50233616")

SQL_CT70_ANY = """
WITH ct_inspecao_final AS (
    SELECT HB.HB_FILIAL, HB.HB_COD AS ct_inspecao, HB.HB_NOME
    FROM SHB010 HB
    WHERE HB.D_E_L_E_T_ = ' '
      AND UPPER(HB.HB_NOME) LIKE '%INSPE%FINAL%'
      AND HB.HB_FILIAL = '01'
)
SELECT
    LTRIM(RTRIM(SH6.H6_PRODUTO)) AS product_code,
    LTRIM(RTRIM(CIF.ct_inspecao)) AS ct,
    LTRIM(RTRIM(CIF.HB_NOME)) AS ct_nome,
    MIN(SH6.H6_DTAPONT) AS first_dt,
    MAX(SH6.H6_DTAPONT) AS last_dt,
    COUNT(*) AS apont_count,
    SUM(CAST(SH6.H6_QTDPROD AS FLOAT)) * 1000 AS total_un
FROM SH6010 SH6
INNER JOIN SH1010 SH1
    ON SH1.H1_FILIAL = SH6.H6_FILIAL
   AND SH1.H1_CODIGO = SH6.H6_RECURSO
   AND SH1.D_E_L_E_T_ = ' '
INNER JOIN ct_inspecao_final CIF
    ON CIF.HB_FILIAL = SH6.H6_FILIAL
   AND CIF.ct_inspecao = SH1.H1_CTRAB
WHERE SH6.D_E_L_E_T_ = ' '
  AND SH6.H6_FILIAL = '01'
  AND SH6.H6_TIPO = 'P'
  AND SH6.H6_PRODUTO IN (?, ?, ?)
GROUP BY SH6.H6_PRODUTO, CIF.ct_inspecao, CIF.HB_NOME
ORDER BY SH6.H6_PRODUTO
"""

SQL_CT70_DETAIL = """
WITH ct_inspecao_final AS (
    SELECT HB.HB_FILIAL, HB.HB_COD AS ct_inspecao, HB.HB_NOME
    FROM SHB010 HB
    WHERE HB.D_E_L_E_T_ = ' '
      AND UPPER(HB.HB_NOME) LIKE '%INSPE%FINAL%'
      AND HB.HB_FILIAL = '01'
)
SELECT TOP 30
    LTRIM(RTRIM(SH6.H6_OP)) AS op,
    LTRIM(RTRIM(SH6.H6_PRODUTO)) AS product_code,
    LTRIM(RTRIM(CIF.ct_inspecao)) AS ct,
    SH6.H6_DTAPONT AS dt_apont,
    CAST(SH6.H6_QTDPROD AS FLOAT) * 1000 AS qtd_un
FROM SH6010 SH6
INNER JOIN SH1010 SH1
    ON SH1.H1_FILIAL = SH6.H6_FILIAL
   AND SH1.H1_CODIGO = SH6.H6_RECURSO
   AND SH1.D_E_L_E_T_ = ' '
INNER JOIN ct_inspecao_final CIF
    ON CIF.HB_FILIAL = SH6.H6_FILIAL
   AND CIF.ct_inspecao = SH1.H1_CTRAB
WHERE SH6.D_E_L_E_T_ = ' '
  AND SH6.H6_FILIAL = '01'
  AND SH6.H6_TIPO = 'P'
  AND SH6.H6_PRODUTO IN (?, ?, ?)
ORDER BY SH6.H6_DTAPONT DESC
"""

SQL_OPS_PLANILHA_CT70 = """
WITH ct_inspecao_final AS (
    SELECT HB.HB_FILIAL, HB.HB_COD AS ct_inspecao
    FROM SHB010 HB
    WHERE HB.D_E_L_E_T_ = ' '
      AND UPPER(HB.HB_NOME) LIKE '%INSPE%FINAL%'
      AND HB.HB_FILIAL = '01'
)
SELECT
    LTRIM(RTRIM(SH6.H6_OP)) AS op,
    LTRIM(RTRIM(SH6.H6_PRODUTO)) AS product_code,
    LTRIM(RTRIM(SH1.H1_CTRAB)) AS ct,
    SH6.H6_DTAPONT AS dt_apont,
    CAST(SH6.H6_QTDPROD AS FLOAT) * 1000 AS qtd_un
FROM SH6010 SH6
INNER JOIN SH1010 SH1
    ON SH1.H1_FILIAL = SH6.H6_FILIAL
   AND SH1.H1_CODIGO = SH6.H6_RECURSO
   AND SH1.D_E_L_E_T_ = ' '
INNER JOIN ct_inspecao_final CIF
    ON CIF.HB_FILIAL = SH6.H6_FILIAL
   AND CIF.ct_inspecao = SH1.H1_CTRAB
WHERE SH6.D_E_L_E_T_ = ' '
  AND SH6.H6_FILIAL = '01'
  AND SH6.H6_TIPO = 'P'
  AND SH6.H6_OP = ?
"""

# OPs amostra da planilha (jan-mar)
SAMPLE_OPS = [
    "24184701001", "24184601001", "24250401001", "24250601001",
    "24322401001", "24184901001", "24185001001", "24250501001",
]


def _fmt_dt(raw) -> str:
    text = str(raw or "").strip()
    if len(text) == 8:
        return f"{text[0:4]}-{text[4:6]}-{text[6:8]}"
    return text or "—"


def main() -> None:
    with PpmQueryRepository() as repo:
        ct70_rows = repo.execute_query(SQL_CT70_ANY, PRODUCTS) or []
        detail = repo.execute_query(SQL_CT70_DETAIL, PRODUCTS) or []

        print("=" * 72)
        print("PIs 50232465 / 50233615 / 50233616 × CT inspeção final (filial 01)")
        print("CT-70 = CT com UPPER(HB_NOME) LIKE '%INSPE%FINAL%'")
        print("=" * 72)

        if not ct70_rows:
            print("\n❌ NENHUM apontamento no CT de inspeção final para esses 3 códigos.")
        else:
            print("\n✓ Apontamentos encontrados no CT inspeção final:")
            for row in ct70_rows:
                print(
                    f"  {row.get('product_code')} | {row.get('ct')} ({row.get('ct_nome')}) | "
                    f"{row.get('apont_count')} apont. | {float(row.get('total_un') or 0):,.0f} un. | "
                    f"{_fmt_dt(row.get('first_dt'))} → {_fmt_dt(row.get('last_dt'))}"
                )

        if detail:
            print("\n--- Detalhe (até 30 apontamentos mais recentes no CT inspeção) ---")
            for row in detail:
                print(
                    f"  OP {row.get('op')} | {row.get('product_code')} | "
                    f"{row.get('ct')} | {_fmt_dt(row.get('dt_apont'))} | "
                    f"{float(row.get('qtd_un') or 0):,.0f} un"
                )

        print("\n--- OPs da planilha (jan-mar): algum apontamento no CT inspeção? ---")
        any_op_ct70 = False
        for op in SAMPLE_OPS:
            rows = repo.execute_query(SQL_OPS_PLANILHA_CT70, (op,)) or []
            if rows:
                any_op_ct70 = True
                print(f"\n  OP {op}: {len(rows)} apont. no CT inspeção")
                for r in rows[:5]:
                    print(
                        f"    {r.get('product_code')} | {r.get('ct')} | "
                        f"{_fmt_dt(r.get('dt_apont'))} | {float(r.get('qtd_un') or 0):,.0f} un"
                    )
            else:
                print(f"  OP {op}: nenhum apontamento no CT inspeção")

        # jan-mai 2026 specifically (PPM period)
        sql_period = SQL_CT70_ANY.replace(
            "GROUP BY",
            "AND SH6.H6_DTAPONT >= '20260101' AND SH6.H6_DTAPONT < '20260601'\nGROUP BY",
        )
        period_rows = repo.execute_query(sql_period, PRODUCTS) or []
        print("\n--- Só jan–mai/2026 (período reconciliação) ---")
        if not period_rows:
            print("  Nenhum apontamento no CT inspeção final.")
        else:
            for row in period_rows:
                print(
                    f"  {row.get('product_code')}: {float(row.get('total_un') or 0):,.0f} un."
                )


if __name__ == "__main__":
    main()
