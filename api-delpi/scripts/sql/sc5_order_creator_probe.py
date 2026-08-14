#!/usr/bin/env python3
"""E1.S1 — Probe SC5 columns that may identify the sales-order creator.

Run inside delpi-api-delpi (TOTVS ODBC). Prints candidate columns, fill rates
for SC (01) and ES (02) samples, and a small distinct-value sample.

Exit 0 even when no useful field is found (discovery outcome).
"""
from __future__ import annotations

import os
import sys

import pyodbc


CANDIDATE_SUBSTRINGS = (
    "USER",
    "USR",
    "UID",
    "USU",
    "INCLUS",
    "INCLUI",
    "CRIAD",
    "AUTHOR",
    "LOGIN",
    "OPERAD",
)


def connect():
    host = os.environ["TOTVS_DB_HOST"]
    port = os.environ.get("TOTVS_DB_PORT", "1433")
    db = os.environ["TOTVS_DB_DATABASE"]
    user = os.environ["TOTVS_DB_USER"]
    pwd = os.environ["TOTVS_DB_PASSWORD"]
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
            return pyodbc.connect(conn_str, timeout=30)
        except Exception as exc:  # noqa: BLE001
            last_err = exc
    raise SystemExit(f"connect failed: {last_err}")


def list_sc5_columns(cur) -> list[str]:
    cur.execute(
        """
        SELECT c.name
        FROM sys.columns c
        INNER JOIN sys.tables t ON t.object_id = c.object_id
        WHERE t.name = N'SC5010'
        ORDER BY c.column_id
        """
    )
    return [str(r[0]).strip() for r in cur.fetchall()]


def candidate_columns(all_cols: list[str]) -> list[str]:
    out: list[str] = []
    for col in all_cols:
        upper = col.upper()
        if any(s in upper for s in CANDIDATE_SUBSTRINGS):
            out.append(col)
    # Always check common Protheus audit names if present
    for extra in (
        "C5_USERLGI",
        "C5_USERLGA",
        "C5_USRINC",
        "C5_USRALT",
        "C5_USER",
        "C5_USUARIO",
        "C5_MSUIDT",
        "USR_ID",
        "USR_CODIGO",
    ):
        if extra in all_cols and extra not in out:
            out.append(extra)
    return out


def probe_sx3(cur) -> None:
    print("\n=== SX3 SC5 user-ish fields ===", flush=True)
    try:
        cur.execute(
            """
            SELECT TOP 50
                RTRIM(X3_CAMPO) AS campo,
                RTRIM(X3_TITULO) AS titulo,
                RTRIM(X3_DESCRIC) AS descricao
            FROM SX3010 WITH (NOLOCK)
            WHERE X3_ARQUIVO = 'SC5'
              AND (
                    X3_CAMPO LIKE '%USU%'
                 OR X3_CAMPO LIKE '%USER%'
                 OR X3_CAMPO LIKE '%USR%'
                 OR X3_TITULO LIKE '%Usu%'
                 OR X3_DESCRIC LIKE '%Usu%'
                 OR X3_TITULO LIKE '%Inclu%'
                 OR X3_DESCRIC LIKE '%Cria%'
              )
            ORDER BY X3_CAMPO
            """
        )
        rows = cur.fetchall()
        if not rows:
            print("(empty)", flush=True)
            return
        for row in rows:
            print(tuple(row), flush=True)
    except Exception as exc:  # noqa: BLE001
        print(f"ERR {type(exc).__name__}: {exc}", flush=True)


def fill_rate(cur, column: str, filial: str, sample: int = 500) -> dict:
    sql = f"""
    SELECT
        COUNT(*) AS n,
        SUM(CASE WHEN NULLIF(LTRIM(RTRIM(CONVERT(VARCHAR(64), {column}))), '') IS NULL THEN 0 ELSE 1 END) AS filled
    FROM (
        SELECT TOP ({sample}) {column}
        FROM SC5010 WITH (NOLOCK)
        WHERE C5_FILIAL = ?
          AND D_E_L_E_T_ = ' '
        ORDER BY R_E_C_N_O_ DESC
    ) s
    """
    cur.execute(sql, (filial,))
    row = cur.fetchone()
    n = int(row[0] or 0)
    filled = int(row[1] or 0)
    rate = (filled / n) if n else 0.0
    return {"filial": filial, "n": n, "filled": filled, "rate": rate}


def sample_values(cur, column: str, filial: str, limit: int = 8) -> list[str]:
    sql = f"""
    SELECT DISTINCT TOP ({limit})
        LTRIM(RTRIM(CONVERT(VARCHAR(64), {column}))) AS v
    FROM SC5010 WITH (NOLOCK)
    WHERE C5_FILIAL = ?
      AND D_E_L_E_T_ = ' '
      AND NULLIF(LTRIM(RTRIM(CONVERT(VARCHAR(64), {column}))), '') IS NOT NULL
    """
    cur.execute(sql, (filial,))
    return [str(r[0]) for r in cur.fetchall()]


def main() -> int:
    conn = connect()
    cur = conn.cursor()
    cols = list_sc5_columns(cur)
    print(f"SC5010 columns={len(cols)}", flush=True)
    print(f"SC5010 all={cols}", flush=True)
    cands = candidate_columns(cols)
    print(f"candidates={cands}", flush=True)
    probe_sx3(cur)
    if not cands:
        print("RESULT: no candidate creator columns on SC5010", flush=True)
        return 0

    useful: list[str] = []
    for col in cands:
        print(f"\n=== {col} ===", flush=True)
        for filial in ("01", "02"):
            try:
                stats = fill_rate(cur, col, filial)
                samples = sample_values(cur, col, filial) if stats["filled"] else []
                print(
                    f"filial={filial} n={stats['n']} filled={stats['filled']} "
                    f"rate={stats['rate']:.1%} samples={samples}",
                    flush=True,
                )
                if stats["rate"] >= 0.5 and stats["filled"] >= 10:
                    useful.append(f"{col}@filial{filial}")
            except Exception as exc:  # noqa: BLE001
                print(f"filial={filial} ERR {type(exc).__name__}: {exc}", flush=True)

    print("\n=== SUMMARY ===", flush=True)
    # C5_MSUIDT is Protheus "Campo UUID" (row technical id), not a human creator.
    human_useful = [u for u in useful if not u.startswith("C5_MSUIDT@")]
    if "C5_MSUIDT" in cands:
        print(
            "NOTE: C5_MSUIDT is SX3 title 'Campo UUID' — technical row id, "
            "not order creator; SYS_USR.USR_UUID does not resolve it.",
            flush=True,
        )
    if human_useful:
        print(f"RESULT: useful_candidates={human_useful}", flush=True)
    else:
        print(
            "RESULT: no human-resolvable creator column on SC5010 "
            "(C5_USER*/USR* absent; C5_MSUIDT not usable as creator)",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
