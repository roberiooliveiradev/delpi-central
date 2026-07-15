#!/usr/bin/env python3
"""Fase 0 — comparar estratégias de custo sem multiplicar linhas SB2."""
from __future__ import annotations

import os

import pyodbc


def main() -> None:
    conn = pyodbc.connect(
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={os.environ['TOTVS_DB_HOST']},{os.environ.get('TOTVS_DB_PORT', '1433')};"
        f"DATABASE={os.environ['TOTVS_DB_DATABASE']};"
        f"UID={os.environ['TOTVS_DB_USER']};PWD={os.environ['TOTVS_DB_PASSWORD']};"
        "TrustServerCertificate=yes;Encrypt=no;",
        timeout=20,
    )
    cur = conn.cursor()
    for label, cost_expr, join in [
        (
            "avg_cm1",
            "COALESCE(NULLIF(CM.AVG_CM1,0), NULLIF(CAST(SB1.B1_CUSTD AS FLOAT),0), 0)",
            """
LEFT JOIN (
  SELECT B2_FILIAL, B2_COD,
         AVG(NULLIF(CAST(B2_CM1 AS FLOAT), 0)) AS AVG_CM1
  FROM SB2010 WITH (NOLOCK)
  WHERE D_E_L_E_T_ = ''
  GROUP BY B2_FILIAL, B2_COD
) CM ON CM.B2_FILIAL = BC.BC_FILIAL AND CM.B2_COD = BC.BC_PRODUTO
""",
        ),
        (
            "b1_only",
            "COALESCE(NULLIF(CAST(SB1.B1_CUSTD AS FLOAT),0), 0)",
            "",
        ),
    ]:
        cur.execute(
            f"""
SELECT COUNT(*) AS N,
       SUM(BC.BC_QUANT * {cost_expr}) AS TOTAL,
       SUM(CASE WHEN {cost_expr}=0 THEN 1 ELSE 0 END) AS SEM
FROM SBC010 BC WITH (NOLOCK)
INNER JOIN SB1010 SB1 WITH (NOLOCK) ON SB1.B1_COD=BC.BC_PRODUTO AND SB1.D_E_L_E_T_=''
{join}
WHERE BC.D_E_L_E_T_='' AND BC.BC_TIPO='R' AND BC.BC_FILIAL='01'
  AND BC.BC_DATA>='20260401' AND BC.BC_DATA<'20260428'
"""
        )
        print(label, dict(zip([d[0] for d in cur.description], cur.fetchone())), flush=True)

    cur.execute(
        """
SELECT SUM(BC.BC_QUANT * COALESCE(NULLIF(CM.AVG_CM1,0), NULLIF(CAST(SB1.B1_CUSTD AS FLOAT),0), 0)) AS DIA
FROM SBC010 BC WITH (NOLOCK)
INNER JOIN SB1010 SB1 WITH (NOLOCK) ON SB1.B1_COD=BC.BC_PRODUTO AND SB1.D_E_L_E_T_=''
LEFT JOIN (
  SELECT B2_FILIAL, B2_COD, AVG(NULLIF(CAST(B2_CM1 AS FLOAT), 0)) AS AVG_CM1
  FROM SB2010 WITH (NOLOCK) WHERE D_E_L_E_T_='' GROUP BY B2_FILIAL, B2_COD
) CM ON CM.B2_FILIAL=BC.BC_FILIAL AND CM.B2_COD=BC.BC_PRODUTO
WHERE BC.D_E_L_E_T_='' AND BC.BC_TIPO='R' AND BC.BC_FILIAL='01' AND BC.BC_DATA='20260427'
"""
    )
    print("dia27", cur.fetchone()[0], flush=True)

    cur.execute("SELECT DISTINCT RTRIM(CYO_FILIAL) AS f FROM CYO010 WHERE D_E_L_E_T_=''")
    print("cyo_filiais", [r[0] for r in cur.fetchall()], flush=True)
    conn.close()


if __name__ == "__main__":
    main()
