"""OPs da planilha PI: apontamento no CT inspeção com QUALQUER produto?"""
from app.infrastructure.persistence.totvs.ppm_repositories.ppm_query_repository import (
    PpmQueryRepository,
)

OPS = [
    "24184701001", "24184601001", "24250401001", "24250601001",
    "24322401001", "24184901001", "24185001001", "24250501001",
    "24250301001",
]

SQL_ANY_PROD_CT70 = """
WITH ct_inspecao_final AS (
    SELECT HB.HB_FILIAL, HB.HB_COD AS ct_inspecao, HB.HB_NOME
    FROM SHB010 HB
    WHERE HB.D_E_L_E_T_ = ' '
      AND UPPER(HB.HB_NOME) LIKE '%INSPE%FINAL%'
      AND HB.HB_FILIAL = '01'
)
SELECT
    LTRIM(RTRIM(SH6.H6_OP)) AS op,
    LTRIM(RTRIM(SH6.H6_PRODUTO)) AS product_code,
    LTRIM(RTRIM(SB1.B1_TIPO)) AS product_type,
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
LEFT JOIN SB1010 SB1
    ON SB1.B1_COD = SH6.H6_PRODUTO
   AND SB1.D_E_L_E_T_ = ' '
WHERE SH6.D_E_L_E_T_ = ' '
  AND SH6.H6_FILIAL = '01'
  AND SH6.H6_TIPO = 'P'
  AND SH6.H6_OP = ?
"""


def main() -> None:
    with PpmQueryRepository() as repo:
        print("OPs da planilha PI — apontamento no CT inspeção (qualquer produto)")
        print("-" * 60)
        for op in OPS:
            rows = repo.execute_query(SQL_ANY_PROD_CT70, (op,)) or []
            if not rows:
                print(f"  {op}: nenhum")
                continue
            print(f"  {op}: {len(rows)} apont. CT inspeção")
            for r in rows:
                print(
                    f"    prod={r.get('product_code')} ({r.get('product_type')}) "
                    f"{r.get('ct')} {_fmt(r.get('dt_apont'))} {float(r.get('qtd_un') or 0):,.0f} un"
                )


def _fmt(raw) -> str:
    t = str(raw or "")
    return f"{t[0:4]}-{t[4:6]}-{t[6:8]}" if len(t) == 8 else t


if __name__ == "__main__":
    main()
