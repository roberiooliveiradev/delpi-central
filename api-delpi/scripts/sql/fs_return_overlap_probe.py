#!/usr/bin/env python3
"""FS-C0.P2-A.1 — probe read-only (NOLOCK) de sobreposição SBC/SD4/SD3 no TOTVS.

Objetivo: provar relações físicas entre perda (SBC), empenho/consumo (SD4) e
movimentos (SD3) para a política híbrida de devolução do Factory Supply.
Apenas SELECTs TOP-limited. Sem escrita.
"""
from __future__ import annotations

import os
import pymssql


def connect():
    for var in ("TOTVS_DB_HOST", "TOTVS_DB_USER", "TOTVS_DB_PASSWORD", "TOTVS_DB_DATABASE"):
        if not os.environ.get(var):
            raise SystemExit(f"missing env var {var}")
    host = os.environ["TOTVS_DB_HOST"]
    port = int(os.environ.get("TOTVS_DB_PORT", "1433"))
    db = os.environ["TOTVS_DB_DATABASE"]
    user = os.environ["TOTVS_DB_USER"]
    pwd = os.environ["TOTVS_DB_PASSWORD"]
    print(f"host={host} db={db} user={user}", flush=True)
    return pymssql.connect(host, user, pwd, db, port=port, login_timeout=15, timeout=60)


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

    run(cur, "SD3 sequence/local columns", """
SELECT name FROM sys.columns
WHERE object_id = OBJECT_ID('SD3010')
  AND (name LIKE 'D3_NUMSEQ%' OR name LIKE 'D3_LOCAL%' OR name LIKE 'D3_DOC%'
       OR name IN ('D3_OP','D3_TM','D3_CF','D3_QUANT','D3_UM','D3_USUARIO','D3_ESTORNO'))
ORDER BY name
""")

    run(cur, "SBC columns incl links", """
SELECT name FROM sys.columns
WHERE object_id = OBJECT_ID('SBC010')
ORDER BY name
""")

    run(cur, "A1. SBC recent sample (R/S)", """
SELECT TOP 15
    RTRIM(BC.BC_FILIAL) AS filial, BC.BC_DATA AS dt, RTRIM(BC.BC_OP) AS op,
    RTRIM(BC.BC_OPERAC) AS operac, RTRIM(BC.BC_PRODUTO) AS mp,
    BC.BC_TIPO AS tipo, BC.BC_QUANT AS qtd, RTRIM(BC.BC_UM) AS um,
    RTRIM(BC.BC_MOTIVO) AS motivo, RTRIM(BC.BC_RECURSO) AS recurso,
    BC.BC_SEQSD3 AS seqsd3, BC.BC_IDENSH6 AS idensh6,
    BC.R_E_C_N_O_ AS recno
FROM SBC010 BC WITH (NOLOCK)
WHERE BC.D_E_L_E_T_ = ' '
  AND BC.BC_DATA >= '20250101'
ORDER BY BC.BC_DATA DESC
""")

    run(cur, "A2. SBC seqsd3/idh6 population by tipo", """
SELECT BC.BC_TIPO AS tipo,
       COUNT(*) AS rows_n,
       SUM(CASE WHEN BC.BC_SEQSD3 IS NULL OR BC.BC_SEQSD3 = 0 THEN 1 ELSE 0 END) AS seq_null,
       SUM(CASE WHEN BC.BC_IDENSH6 IS NULL OR BC.BC_IDENSH6 = 0 THEN 1 ELSE 0 END) AS idh6_null
FROM SBC010 BC WITH (NOLOCK)
WHERE BC.D_E_L_E_T_ = ' ' AND BC.BC_DATA >= '20250101'
GROUP BY BC.BC_TIPO
""")

    run(cur, "B. SBC -> SD3 via NUMSEQ+OP (TM/CF/LOCAL/quant)", """
SELECT TOP 20
    RTRIM(BC.BC_FILIAL) AS filial, RTRIM(BC.BC_OP) AS op, RTRIM(BC.BC_PRODUTO) AS mp,
    BC.BC_TIPO AS tipo, BC.BC_QUANT AS sbc_qtd, BC.BC_SEQSD3 AS seqsd3,
    RTRIM(SD3.D3_TM) AS d3_tm, RTRIM(SD3.D3_CF) AS d3_cf,
    RTRIM(SD3.D3_LOCAL) AS d3_local, SD3.D3_QUANT AS d3_qtd,
    RTRIM(SD3.D3_OP) AS d3_op, RTRIM(SD3.D3_DOC) AS d3_doc,
    SD3.D3_NUMSEQ AS d3_numseq, RTRIM(SD3.D3_ESTORNO) AS estorno
FROM SBC010 BC WITH (NOLOCK)
INNER JOIN SD3010 SD3 WITH (NOLOCK)
    ON SD3.D3_FILIAL = BC.BC_FILIAL
   AND SD3.D3_NUMSEQ = BC.BC_SEQSD3
   AND SD3.D3_OP = BC.BC_OP
   AND SD3.D3_COD = BC.BC_PRODUTO
   AND SD3.D_E_L_E_T_ = ' '
WHERE BC.D_E_L_E_T_ = ' ' AND BC.BC_DATA >= '20250101'
ORDER BY BC.BC_DATA DESC
""")

    run(cur, "B2. SBC -> SD3 via RECNO", """
SELECT TOP 10
    BC.BC_TIPO AS tipo, BC.BC_QUANT AS sbc_qtd, BC.BC_SEQSD3 AS seqsd3,
    SD3.R_E_C_N_O_ AS d3_recno, RTRIM(SD3.D3_TM) AS tm, RTRIM(SD3.D3_CF) AS cf,
    RTRIM(SD3.D3_LOCAL) AS local, SD3.D3_QUANT AS d3_qtd, RTRIM(SD3.D3_OP) AS d3_op
FROM SBC010 BC WITH (NOLOCK)
INNER JOIN SD3010 SD3 WITH (NOLOCK) ON SD3.R_E_C_N_O_ = BC.BC_SEQSD3
WHERE BC.D_E_L_E_T_ = ' ' AND BC.BC_DATA >= '20250101'
""")

    run(cur, "C. SD3 census by (filial,local,tm,cf) since 2025-08", """
SELECT RTRIM(D3.D3_FILIAL) AS filial, RTRIM(D3.D3_LOCAL) AS local,
       RTRIM(D3.D3_TM) AS tm, RTRIM(D3.D3_CF) AS cf,
       COUNT(*) AS n,
       SUM(CASE WHEN RTRIM(ISNULL(D3.D3_OP,'')) <> '' THEN 1 ELSE 0 END) AS with_op,
       SUM(D3.D3_QUANT) AS qtd
FROM SD3010 D3 WITH (NOLOCK)
WHERE D3.D_E_L_E_T_ = ' ' AND D3.D3_EMISSAO >= '20250801'
  AND RTRIM(ISNULL(D3.D3_ESTORNO,'')) <> 'S'
GROUP BY D3.D3_FILIAL, D3.D3_LOCAL, D3.D3_TM, D3.D3_CF
ORDER BY D3.D3_FILIAL, D3.D3_LOCAL, n DESC
""")

    run(cur, "D. OPs com perda: SD4 vs SD3-saida99 vs SBC (overlap)", """
WITH LOST AS (
    SELECT BC.BC_FILIAL, BC.BC_OP, BC.BC_PRODUTO,
           SUM(BC.BC_QUANT) AS sbc_qtd
    FROM SBC010 BC WITH (NOLOCK)
    WHERE BC.D_E_L_E_T_ = ' ' AND BC.BC_DATA >= '20250101'
      AND BC.BC_TIPO IN ('R','S')
    GROUP BY BC.BC_FILIAL, BC.BC_OP, BC.BC_PRODUTO
)
SELECT TOP 15
    RTRIM(L.BC_FILIAL) AS filial, RTRIM(L.BC_OP) AS op, RTRIM(L.BC_PRODUTO) AS mp,
    L.sbc_qtd,
    SUM(D4.D4_QTDEORI) AS d4_qtdeori, SUM(D4.D4_QUANT) AS d4_quant,
    SUM(D4.D4_QTDEORI - D4.D4_QUANT) AS d4_consumed,
    (SELECT SUM(X.D3_QUANT) FROM SD3010 X WITH (NOLOCK)
      WHERE X.D_E_L_E_T_ = ' ' AND X.D3_FILIAL = L.BC_FILIAL AND X.D3_OP = L.BC_OP
        AND X.D3_COD = L.BC_PRODUTO AND X.D3_LOCAL = '99' AND X.D3_TM >= '500'
        AND RTRIM(ISNULL(X.D3_ESTORNO,'')) <> 'S') AS sd3_saida99,
    (SELECT SUM(X.D3_QUANT) FROM SD3010 X WITH (NOLOCK)
      WHERE X.D_E_L_E_T_ = ' ' AND X.D3_FILIAL = L.BC_FILIAL AND X.D3_OP = L.BC_OP
        AND X.D3_COD = L.BC_PRODUTO AND X.D3_LOCAL = '99' AND X.D3_TM < '500'
        AND RTRIM(ISNULL(X.D3_ESTORNO,'')) <> 'S') AS sd3_entrada99
FROM LOST L
INNER JOIN SD4010 D4 WITH (NOLOCK)
    ON D4.D4_FILIAL = L.BC_FILIAL AND D4.D4_OP = L.BC_OP AND D4.D4_COD = L.BC_PRODUTO
   AND D4.D_E_L_E_T_ = ' '
GROUP BY L.BC_FILIAL, L.BC_OP, L.BC_PRODUTO, L.sbc_qtd
ORDER BY L.sbc_qtd DESC
""")

    conn.close()


if __name__ == "__main__":
    main()
