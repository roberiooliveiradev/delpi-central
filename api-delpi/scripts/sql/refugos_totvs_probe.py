#!/usr/bin/env python3
"""Fase 0 — probe direto no TOTVS (pyodbc), sem depender da API HTTP."""
from __future__ import annotations

import os
import sys

import pyodbc


def connect():
    host = os.environ["TOTVS_DB_HOST"]
    port = os.environ.get("TOTVS_DB_PORT", "1433")
    db = os.environ["TOTVS_DB_DATABASE"]
    user = os.environ["TOTVS_DB_USER"]
    pwd = os.environ["TOTVS_DB_PASSWORD"]
    print(f"host={host} port={port} db={db} user={user}", flush=True)
    print("drivers=", pyodbc.drivers(), flush=True)
    last_err = None
    for driver in ("ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server", "FreeTDS"):
        if driver == "FreeTDS":
            conn_str = (
                f"DRIVER={{FreeTDS}};SERVER={host};PORT={port};DATABASE={db};"
                f"UID={user};PWD={pwd};TDS_Version=7.4;"
            )
        else:
            conn_str = (
                f"DRIVER={{{driver}}};SERVER={host},{port};DATABASE={db};UID={user};PWD={pwd};"
                "TrustServerCertificate=yes;Encrypt=no;"
            )
        try:
            conn = pyodbc.connect(conn_str, timeout=20)
            print("connected with", driver, flush=True)
            return conn
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            print(f"fail {driver}: {type(exc).__name__}: {exc}", flush=True)
    raise SystemExit(f"connect failed: {last_err}")


def main() -> None:
    conn = connect()
    cur = conn.cursor()

    probes = [
        ("CYO tables", "SELECT TOP 5 name FROM sys.tables WHERE name LIKE 'CYO%' ORDER BY name"),
        ("SYS_USR", "SELECT TOP 1 name FROM sys.tables WHERE name LIKE 'SYS_USR%' ORDER BY name"),
        (
            "BC_OPER columns",
            "SELECT name FROM sys.columns WHERE object_id = OBJECT_ID('SBC010') AND name LIKE 'BC_OPER%' ORDER BY name",
        ),
        (
            "BC_MOTIVO / RECURSO",
            "SELECT name FROM sys.columns WHERE object_id = OBJECT_ID('SBC010') AND name IN ('BC_MOTIVO','BC_RECURSO','BC_OPERADO','BC_OP','BC_QUANT','BC_PRODUTO','BC_TIPO','BC_DATA','BC_FILIAL') ORDER BY name",
        ),
        (
            "CYO columns",
            "SELECT name FROM sys.columns WHERE object_id = OBJECT_ID('CYO010') ORDER BY name",
        ),
    ]
    for label, sql in probes:
        print(f"\n=== {label} ===", flush=True)
        try:
            cur.execute(sql)
            rows = cur.fetchall()
            for r in rows:
                print(tuple(r), flush=True)
            if not rows:
                print("(empty)", flush=True)
        except Exception as exc:  # noqa: BLE001
            print(f"ERR {type(exc).__name__}: {exc}", flush=True)

    print("\n=== sample joins ===", flush=True)
    cur.execute(
        """
SELECT TOP 5
    BC.BC_FILIAL,
    BC.BC_DATA,
    RTRIM(BC.BC_OP) AS OP,
    RTRIM(BC.BC_PRODUTO) AS MP,
    RTRIM(BC.BC_MOTIVO) AS MOTIVO,
    BC.BC_QUANT,
    RTRIM(BC.BC_RECURSO) AS RECURSO,
    RTRIM(BC.BC_OPERADO) AS OPERADO,
    RTRIM(SB1.B1_DESC) AS DESC_MP,
    SB1.B1_CUSTD,
    SB2.B2_CM1,
    RTRIM(OP.C2_PRODUTO) AS PA,
    BC.BC_QUANT * COALESCE(NULLIF(CAST(SB2.B2_CM1 AS FLOAT), 0), NULLIF(CAST(SB1.B1_CUSTD AS FLOAT), 0), 0) AS VALOR
FROM SBC010 BC WITH (NOLOCK)
INNER JOIN SB1010 SB1 WITH (NOLOCK)
    ON SB1.B1_COD = BC.BC_PRODUTO AND SB1.D_E_L_E_T_ = ''
LEFT JOIN SB2010 SB2 WITH (NOLOCK)
    ON SB2.B2_FILIAL = BC.BC_FILIAL AND SB2.B2_COD = BC.BC_PRODUTO AND SB2.D_E_L_E_T_ = ''
LEFT JOIN SC2010 OP WITH (NOLOCK)
    ON OP.C2_FILIAL = BC.BC_FILIAL AND OP.C2_OP = BC.BC_OP AND OP.D_E_L_E_T_ = ''
WHERE BC.D_E_L_E_T_ = '' AND BC.BC_TIPO = 'R'
  AND BC.BC_DATA >= '20260401' AND BC.BC_DATA < '20260428'
ORDER BY BC.BC_DATA DESC
"""
    )
    cols = [d[0] for d in cur.description]
    for row in cur.fetchall():
        print(dict(zip(cols, row)), flush=True)

    # Try CYO join if table exists
    print("\n=== CYO join ===", flush=True)
    try:
        cur.execute(
            """
SELECT TOP 5
    RTRIM(BC.BC_MOTIVO) AS COD,
    RTRIM(CYO.CYO_DSRF) AS MOTIVO,
    SUM(BC.BC_QUANT * COALESCE(NULLIF(CAST(SB2.B2_CM1 AS FLOAT), 0), NULLIF(CAST(SB1.B1_CUSTD AS FLOAT), 0), 0)) AS VALOR
FROM SBC010 BC WITH (NOLOCK)
INNER JOIN SB1010 SB1 WITH (NOLOCK)
    ON SB1.B1_COD = BC.BC_PRODUTO AND SB1.D_E_L_E_T_ = ''
LEFT JOIN SB2010 SB2 WITH (NOLOCK)
    ON SB2.B2_FILIAL = BC.BC_FILIAL AND SB2.B2_COD = BC.BC_PRODUTO AND SB2.D_E_L_E_T_ = ''
LEFT JOIN CYO010 CYO WITH (NOLOCK)
    ON CYO.CYO_CDRF = BC.BC_MOTIVO AND CYO.D_E_L_E_T_ = ''
WHERE BC.D_E_L_E_T_ = '' AND BC.BC_TIPO = 'R'
  AND BC.BC_FILIAL = '01'
  AND BC.BC_DATA >= '20260401' AND BC.BC_DATA < '20260428'
GROUP BY RTRIM(BC.BC_MOTIVO), RTRIM(CYO.CYO_DSRF)
ORDER BY VALOR DESC
"""
        )
        cols = [d[0] for d in cur.description]
        for row in cur.fetchall():
            print(dict(zip(cols, row)), flush=True)
    except Exception as exc:  # noqa: BLE001
        print(f"CYO ERR {type(exc).__name__}: {exc}", flush=True)

    # SYS_USR join
    print("\n=== SYS_USR join ===", flush=True)
    try:
        cur.execute(
            """
SELECT TOP 5
    RTRIM(BC.BC_OPERADO) AS COD,
    RTRIM(U.USR_NOME) AS NOME,
    SUM(BC.BC_QUANT * COALESCE(NULLIF(CAST(SB2.B2_CM1 AS FLOAT), 0), NULLIF(CAST(SB1.B1_CUSTD AS FLOAT), 0), 0)) AS VALOR
FROM SBC010 BC WITH (NOLOCK)
INNER JOIN SB1010 SB1 WITH (NOLOCK)
    ON SB1.B1_COD = BC.BC_PRODUTO AND SB1.D_E_L_E_T_ = ''
LEFT JOIN SB2010 SB2 WITH (NOLOCK)
    ON SB2.B2_FILIAL = BC.BC_FILIAL AND SB2.B2_COD = BC.BC_PRODUTO AND SB2.D_E_L_E_T_ = ''
LEFT JOIN SYS_USR U WITH (NOLOCK)
    ON U.USR_ID = BC.BC_OPERADO
WHERE BC.D_E_L_E_T_ = '' AND BC.BC_TIPO = 'R'
  AND BC.BC_FILIAL = '01'
  AND BC.BC_DATA >= '20260401' AND BC.BC_DATA < '20260428'
  AND RTRIM(BC.BC_OPERADO) <> ''
GROUP BY RTRIM(BC.BC_OPERADO), RTRIM(U.USR_NOME)
ORDER BY VALOR DESC
"""
        )
        cols = [d[0] for d in cur.description]
        for row in cur.fetchall():
            print(dict(zip(cols, row)), flush=True)
    except Exception as exc:  # noqa: BLE001
        print(f"SYS_USR ERR {type(exc).__name__}: {exc}", flush=True)

    print("\n=== resumo filial 01 ===", flush=True)
    cur.execute(
        """
SELECT
    SUM(BC.BC_QUANT * COALESCE(NULLIF(CAST(SB2.B2_CM1 AS FLOAT), 0), NULLIF(CAST(SB1.B1_CUSTD AS FLOAT), 0), 0)) AS TOTAL_VALOR,
    SUM(BC.BC_QUANT) AS TOTAL_QTD,
    COUNT(*) AS OCORRENCIAS,
    SUM(CASE WHEN COALESCE(NULLIF(CAST(SB2.B2_CM1 AS FLOAT), 0), NULLIF(CAST(SB1.B1_CUSTD AS FLOAT), 0), 0) = 0 THEN 1 ELSE 0 END) AS SEM_CUSTO
FROM SBC010 BC WITH (NOLOCK)
INNER JOIN SB1010 SB1 WITH (NOLOCK)
    ON SB1.B1_COD = BC.BC_PRODUTO AND SB1.D_E_L_E_T_ = ''
LEFT JOIN SB2010 SB2 WITH (NOLOCK)
    ON SB2.B2_FILIAL = BC.BC_FILIAL AND SB2.B2_COD = BC.BC_PRODUTO AND SB2.D_E_L_E_T_ = ''
WHERE BC.D_E_L_E_T_ = '' AND BC.BC_TIPO = 'R'
  AND BC.BC_FILIAL = '01'
  AND BC.BC_DATA >= '20260401' AND BC.BC_DATA < '20260428'
"""
    )
    cols = [d[0] for d in cur.description]
    print(dict(zip(cols, cur.fetchone())), flush=True)

    conn.close()
    print("OK", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"FATAL {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        raise
