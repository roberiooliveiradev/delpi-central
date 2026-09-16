#!/usr/bin/env python3
"""Sonda — saldo por operação (SH6) vs cabeçalho da OP (SC2) na carga máquina.

Comprova a chave H6_OPERAC × H8_OPER, o SUM(H6_QTDPROD) da operação relatada
e o custo do agregado filtrado por filial + lista de OPs.

Uso (mesmo padrão das sondas SH6):
  TOTVS_DB_HOST=... TOTVS_DB_DATABASE=... TOTVS_DB_USER=... TOTVS_DB_PASSWORD=... \\
    python api-delpi/scripts/sql/machine_load_operation_balance_probe.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from typing import Any

import pyodbc

BRANCH = os.environ.get("PROBE_BRANCH", "02")
ORDER = os.environ.get("PROBE_OP", "10964501004")
OPERATION = os.environ.get("PROBE_OPERATION", "01")


def connect() -> pyodbc.Connection:
    host = os.environ["TOTVS_DB_HOST"]
    port = os.environ.get("TOTVS_DB_PORT", "1433")
    db = os.environ["TOTVS_DB_DATABASE"]
    user = os.environ["TOTVS_DB_USER"]
    pwd = os.environ["TOTVS_DB_PASSWORD"]
    print(f"host={host} port={port} db={db} user={user}", flush=True)
    print(f"branch={BRANCH} order={ORDER} operation={OPERATION}", flush=True)
    last_err: Exception | None = None
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
            conn = pyodbc.connect(conn_str, timeout=30)
            print("connected with", driver, flush=True)
            return conn
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            print(f"fail {driver}: {type(exc).__name__}: {exc}", flush=True)
    raise SystemExit(f"connect failed: {last_err}")


def rows_as_dicts(cur: pyodbc.Cursor) -> list[dict[str, Any]]:
    cols = [c[0] for c in (cur.description or [])]
    out: list[dict[str, Any]] = []
    for row in cur.fetchall():
        item: dict[str, Any] = {}
        for i, col in enumerate(cols):
            val = row[i]
            if hasattr(val, "isoformat"):
                val = val.isoformat()
            elif isinstance(val, bytes):
                val = val.decode("latin-1", errors="replace")
            elif isinstance(val, str):
                val = val.rstrip()
            item[col] = val
        out.append(item)
    return out


def run_probe(cur: pyodbc.Cursor, name: str, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any]:
    print(f"\n{'=' * 60}\nPROBE: {name}\n{'=' * 60}", flush=True)
    t0 = time.perf_counter()
    cur.execute(sql, params)
    data = rows_as_dicts(cur)
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
    print(f"rows={len(data)} elapsed_ms={elapsed_ms}", flush=True)
    for row in data[:25]:
        print(json.dumps(row, ensure_ascii=False, default=str), flush=True)
    return {"name": name, "rows": len(data), "elapsed_ms": elapsed_ms, "sample": data[:10]}


def main() -> None:
    conn = connect()
    cur = conn.cursor()
    results: list[dict[str, Any]] = []

    results.append(
        run_probe(
            cur,
            "header_vs_allocation_keys",
            """
SELECT
    LTRIM(RTRIM(OP.C2_OP)) AS production_order,
    CAST(OP.C2_QUANT AS FLOAT) AS planned_qty,
    CAST(OP.C2_QUJE AS FLOAT) AS produced_qty,
    CAST(OP.C2_QUANT - OP.C2_QUJE AS FLOAT) AS header_pending_qty,
    NULLIF(LTRIM(RTRIM(OP.C2_DATRF)), '') AS finish_date,
    LTRIM(RTRIM(OA.H8_OPER)) AS h8_oper,
    LEN(OA.H8_OPER) AS h8_oper_len,
    DATALENGTH(OA.H8_OPER) AS h8_oper_bytes
FROM SC2010 OP WITH (NOLOCK)
LEFT JOIN SH8010 OA WITH (NOLOCK)
    ON OA.H8_FILIAL = OP.C2_FILIAL
   AND OA.H8_OP = OP.C2_OP
   AND OA.D_E_L_E_T_ = ''
WHERE OP.D_E_L_E_T_ = ''
  AND OP.C2_FILIAL = ?
  AND LTRIM(RTRIM(OP.C2_OP)) = ?
""",
            (BRANCH, ORDER),
        )
    )

    results.append(
        run_probe(
            cur,
            "sh6_keys_and_sum",
            """
SELECT
    LTRIM(RTRIM(AH.H6_OP)) AS production_order,
    LTRIM(RTRIM(AH.H6_OPERAC)) AS h6_operac,
    LEN(AH.H6_OPERAC) AS h6_operac_len,
    DATALENGTH(AH.H6_OPERAC) AS h6_operac_bytes,
    AH.H6_TIPO AS appointment_type,
    CAST(SUM(CAST(AH.H6_QTDPROD AS FLOAT)) AS DECIMAL(18, 6)) AS produced_qty,
    CAST(SUM(CAST(AH.H6_QTDPERD AS FLOAT)) AS DECIMAL(18, 6)) AS scrap_qty,
    COUNT(*) AS appointment_count
FROM SH6010 AH WITH (NOLOCK)
WHERE AH.D_E_L_E_T_ = ''
  AND AH.H6_TIPO = 'P'
  AND AH.H6_FILIAL = CAST(? AS CHAR(2))
  AND AH.H6_OP = CAST(? AS CHAR(14))
GROUP BY AH.H6_OP, AH.H6_OPERAC, AH.H6_TIPO
ORDER BY AH.H6_OPERAC
""",
            (BRANCH, ORDER),
        )
    )

    results.append(
        run_probe(
            cur,
            "join_without_trim",
            """
SELECT
    LTRIM(RTRIM(OA.H8_OPER)) AS operation_code,
    CAST(ISNULL(OPQ.produced_qty, 0) AS DECIMAL(18, 6)) AS operation_produced_qty
FROM SH8010 OA WITH (NOLOCK)
OUTER APPLY (
    SELECT SUM(CAST(AH.H6_QTDPROD AS FLOAT)) AS produced_qty
    FROM SH6010 AH WITH (NOLOCK)
    WHERE AH.D_E_L_E_T_ = ''
      AND AH.H6_TIPO = 'P'
      AND AH.H6_FILIAL = OA.H8_FILIAL
      AND AH.H6_OP = OA.H8_OP
      AND AH.H6_OPERAC = OA.H8_OPER
) OPQ
WHERE OA.D_E_L_E_T_ = ''
  AND OA.H8_FILIAL = ?
  AND OA.H8_OP = ?
""",
            (BRANCH, ORDER),
        )
    )

    results.append(
        run_probe(
            cur,
            "aggregate_cost_cast_char",
            """
SELECT
    LTRIM(RTRIM(AH.H6_OP)) AS production_order,
    LTRIM(RTRIM(AH.H6_OPERAC)) AS operation_code,
    CAST(SUM(CAST(AH.H6_QTDPROD AS FLOAT)) AS DECIMAL(18, 6)) AS operation_produced_qty
FROM SH6010 AH WITH (NOLOCK)
WHERE AH.D_E_L_E_T_ = ''
  AND AH.H6_TIPO = 'P'
  AND AH.H6_FILIAL = CAST(? AS CHAR(2))
  AND AH.H6_OP IN (CAST(? AS CHAR(14)))
GROUP BY AH.H6_OP, AH.H6_OPERAC
""",
            (BRANCH, ORDER),
        )
    )

    conn.close()
    out_path = os.environ.get("PROBE_OUT")
    if out_path:
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(
                {"branch": BRANCH, "order": ORDER, "results": results},
                fh,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        print(f"wrote {out_path}", flush=True)
    print(json.dumps({"results": results}, ensure_ascii=False, default=str), flush=True)


if __name__ == "__main__":
    try:
        main()
    except KeyError as exc:
        print(f"missing env {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
