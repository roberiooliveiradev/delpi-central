#!/usr/bin/env python3
"""FS-C0.P2-A.1 — round 2: tipos SBC, pairing de transferência/devolução, TM999."""
from __future__ import annotations

import os
import pymssql


def connect():
    for var in ("TOTVS_DB_HOST", "TOTVS_DB_USER", "TOTVS_DB_PASSWORD", "TOTVS_DB_DATABASE"):
        if not os.environ.get(var):
            raise SystemExit(f"missing env var {var}")
    return pymssql.connect(
        os.environ["TOTVS_DB_HOST"],
        os.environ["TOTVS_DB_USER"],
        os.environ["TOTVS_DB_PASSWORD"],
        os.environ["TOTVS_DB_DATABASE"],
        port=int(os.environ.get("TOTVS_DB_PORT", "1433")),
        login_timeout=15, timeout=90,
    )


def run(cur, label, sql):
    print(f"\n===== {label} =====", flush=True)
    try:
        cur.execute(sql)
        cols = [d[0] for d in cur.description]
        print(" | ".join(cols), flush=True)
        n = 0
        for row in cur.fetchall():
            print(" | ".join("" if v is None else str(v) for v in row), flush=True)
            n += 1
        print(f"-- {n} rows", flush=True)
    except Exception as exc:  # noqa: BLE001
        print(f"ERR {type(exc).__name__}: {exc}", flush=True)


def main() -> None:
    conn = connect()
    cur = conn.cursor()

    run(cur, "A1. SBC sample R e S", """
SELECT TOP 10
    RTRIM(BC.BC_FILIAL) AS filial, BC.BC_DATA AS dt, RTRIM(BC.BC_OP) AS op,
    RTRIM(BC.BC_OPERAC) AS operac, RTRIM(BC.BC_PRODUTO) AS mp,
    BC.BC_TIPO AS tipo, BC.BC_QUANT AS qtd,
    RTRIM(BC.BC_MOTIVO) AS motivo, RTRIM(BC.BC_RECURSO) AS recurso,
    RTRIM(BC.BC_SEQSD3) AS seqsd3, BC.BC_IDENSH6 AS idensh6
FROM SBC010 BC WITH (NOLOCK)
WHERE BC.D_E_L_E_T_ = ' ' AND BC.BC_DATA >= '20250101'
ORDER BY BC.BC_TIPO, BC.BC_DATA DESC
""")

    run(cur, "A2. SBC population by tipo (varchar-safe)", """
SELECT RTRIM(BC.BC_TIPO) AS tipo, COUNT(*) AS rows_n,
       SUM(CASE WHEN LTRIM(RTRIM(ISNULL(BC.BC_SEQSD3,''))) = '' THEN 1 ELSE 0 END) AS seq_null,
       SUM(CASE WHEN BC.BC_IDENSH6 IS NULL OR BC.BC_IDENSH6 = 0 THEN 1 ELSE 0 END) AS idh6_null
FROM SBC010 BC WITH (NOLOCK)
WHERE BC.D_E_L_E_T_ = ' ' AND BC.BC_DATA >= '20250101'
GROUP BY BC.BC_TIPO
""")

    run(cur, "E. pairing: docs com linhas em 01 e 99 (transfer/devolucao)", """
WITH MOV AS (
    SELECT RTRIM(D3.D3_FILIAL) AS filial, RTRIM(D3.D3_DOC) AS doc,
           RTRIM(D3.D3_LOCAL) AS local, RTRIM(D3.D3_TM) AS tm, RTRIM(D3.D3_CF) AS cf,
           RTRIM(D3.D3_COD) AS cod, D3.D3_QUANT AS qtd,
           RTRIM(ISNULL(D3.D3_OP,'')) AS op, RTRIM(D3.D3_LOCALIZ) AS localiz,
           D3.D3_EMISSAO AS emissao, RTRIM(ISNULL(D3.D3_USUARIO,'')) AS usr
    FROM SD3010 D3 WITH (NOLOCK)
    WHERE D3.D_E_L_E_T_ = ' ' AND D3.D3_EMISSAO >= '20260101'
      AND RTRIM(ISNULL(D3.D3_ESTORNO,'')) <> 'S'
      AND RTRIM(ISNULL(D3.D3_DOC,'')) <> ''
)
SELECT filial, doc, cod, COUNT(*) AS linhas,
       COUNT(DISTINCT local) AS locais,
       MAX(local) AS loc_max, MIN(local) AS loc_min,
       MAX(tm) AS tm_max, MIN(tm) AS tm_min, MAX(cf) AS cf
FROM MOV
GROUP BY filial, doc, cod
HAVING COUNT(DISTINCT local) > 1
   AND MAX(local) <> MIN(local)
ORDER BY filial, doc
""")

    run(cur, "E2. detalhe de docs multi-local recentes", """
SELECT TOP 40
    RTRIM(D3.D3_FILIAL) AS filial, RTRIM(D3.D3_DOC) AS doc,
    RTRIM(D3.D3_LOCAL) AS local, RTRIM(D3.D3_LOCALIZ) AS localiz,
    RTRIM(D3.D3_TM) AS tm, RTRIM(D3.D3_CF) AS cf,
    RTRIM(D3.D3_COD) AS cod, D3.D3_QUANT AS qtd,
    RTRIM(ISNULL(D3.D3_OP,'')) AS op, D3.D3_EMISSAO AS dt,
    RTRIM(ISNULL(D3.D3_USUARIO,'')) AS usr
FROM SD3010 D3 WITH (NOLOCK)
WHERE D3.D_E_L_E_T_ = ' ' AND D3.D3_EMISSAO >= '20260801'
  AND RTRIM(ISNULL(D3.D3_ESTORNO,'')) <> 'S'
  AND D3.D3_DOC IN (
      SELECT TOP 12 D3_DOC FROM SD3010 WITH (NOLOCK)
      WHERE D_E_L_E_T_ = ' ' AND D3_EMISSAO >= '20260801'
        AND D3_LOCAL IN ('01','99')
      GROUP BY D3_DOC
      HAVING COUNT(DISTINCT D3_LOCAL) > 1
      ORDER BY MAX(D3_EMISSAO) DESC)
ORDER BY doc, local, tm
""")

    run(cur, "F. census entrada@99 (quem entra na fabrica) since 2025-08", """
SELECT RTRIM(D3.D3_FILIAL) AS filial, RTRIM(D3.D3_LOCAL) AS local,
       RTRIM(D3.D3_TM) AS tm, RTRIM(D3.D3_CF) AS cf, COUNT(*) AS n,
       SUM(CASE WHEN RTRIM(ISNULL(D3.D3_OP,'')) <> '' THEN 1 ELSE 0 END) AS with_op,
       SUM(D3.D3_QUANT) AS qtd
FROM SD3010 D3 WITH (NOLOCK)
WHERE D3.D_E_L_E_T_ = ' ' AND D3.D3_EMISSAO >= '20250801'
  AND RTRIM(ISNULL(D3.D3_ESTORNO,'')) <> 'S'
  AND D3.D3_TM < '500'
GROUP BY D3.D3_FILIAL, D3.D3_LOCAL, D3.D3_TM, D3.D3_CF
ORDER BY n DESC
""")

    run(cur, "G. saida@99 (o que sai da fabrica) por CF since 2025-08", """
SELECT RTRIM(D3.D3_FILIAL) AS filial, RTRIM(D3.D3_LOCAL) AS local,
       RTRIM(D3.D3_TM) AS tm, RTRIM(D3.D3_CF) AS cf, COUNT(*) AS n,
       SUM(CASE WHEN RTRIM(ISNULL(D3.D3_OP,'')) <> '' THEN 1 ELSE 0 END) AS with_op,
       SUM(D3.D3_QUANT) AS qtd
FROM SD3010 D3 WITH (NOLOCK)
WHERE D3.D_E_L_E_T_ = ' ' AND D3.D3_EMISSAO >= '20250801'
  AND RTRIM(ISNULL(D3.D3_ESTORNO,'')) <> 'S'
  AND D3.D3_LOCAL = '99' AND D3.D3_TM >= '500'
GROUP BY D3.D3_FILIAL, D3.D3_LOCAL, D3.D3_TM, D3.D3_CF
ORDER BY D3.D3_FILIAL, n DESC
""")

    conn.close()


if __name__ == "__main__":
    main()
