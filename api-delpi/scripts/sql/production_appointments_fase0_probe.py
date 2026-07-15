#!/usr/bin/env python3
"""Fase 0 — probes SQL Apontamento de Produção (SH6→SH1→SHB) via pyodbc direto no TOTVS."""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import date, timedelta
from typing import Any

import pyodbc

# Período padrão: últimos 30 dias (datas Protheus AAAAMMDD).
_TODAY = date.today()
DATE_END_EXCL = (_TODAY + timedelta(days=1)).strftime("%Y%m%d")
DATE_START = (_TODAY - timedelta(days=30)).strftime("%Y%m%d")
BRANCH = os.environ.get("PROBE_BRANCH", "01")

CT_INSPECAO_LIKE = "%INSPE%FINAL%"


def connect() -> pyodbc.Connection:
    host = os.environ["TOTVS_DB_HOST"]
    port = os.environ.get("TOTVS_DB_PORT", "1433")
    db = os.environ["TOTVS_DB_DATABASE"]
    user = os.environ["TOTVS_DB_USER"]
    pwd = os.environ["TOTVS_DB_PASSWORD"]
    print(f"host={host} port={port} db={db} user={user}", flush=True)
    print(f"period={DATE_START}..{DATE_END_EXCL} branch={BRANCH}", flush=True)
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
    if len(data) > 25:
        print(f"... ({len(data) - 25} more)", flush=True)
    return {"name": name, "rows": len(data), "elapsed_ms": elapsed_ms, "sample": data[:10]}


PROBES: dict[str, tuple[str, tuple[Any, ...]]] = {
    "catalog_cts": (
        f"""
SELECT
    RTRIM(HB.HB_FILIAL) AS branch,
    RTRIM(HB.HB_COD) AS work_center,
    RTRIM(HB.HB_NOME) AS name,
    CASE
        WHEN UPPER(HB.HB_NOME) LIKE '{CT_INSPECAO_LIKE}' THEN 1
        ELSE 0
    END AS is_final_inspection
FROM SHB010 HB WITH (NOLOCK)
WHERE HB.D_E_L_E_T_ = ' '
  AND HB.HB_FILIAL = ?
ORDER BY HB.HB_COD
""",
        (BRANCH,),
    ),
    "cts_inspecao_final": (
        f"""
SELECT
    RTRIM(HB_FILIAL) AS branch,
    RTRIM(HB_COD) AS work_center,
    RTRIM(HB_NOME) AS name
FROM SHB010 WITH (NOLOCK)
WHERE D_E_L_E_T_ = ' '
  AND UPPER(HB_NOME) LIKE '{CT_INSPECAO_LIKE}'
ORDER BY HB_FILIAL, HB_COD
""",
        (),
    ),
    "appointments_sample": (
        """
SELECT TOP 20
    RTRIM(SH6.H6_FILIAL) AS branch,
    RTRIM(SH6.H6_OP) AS production_order,
    RTRIM(SH6.H6_PRODUTO) AS product,
    RTRIM(SB1.B1_TIPO) AS product_type,
    RTRIM(SH1.H1_CTRAB) AS work_center,
    RTRIM(HB.HB_NOME) AS work_center_name,
    RTRIM(SH6.H6_OPERAC) AS operation,
    RTRIM(SH6.H6_RECURSO) AS resource,
    CAST(SH6.H6_QTDPROD AS FLOAT) AS qty_produced,
    CAST(SH6.H6_QTDPERD AS FLOAT) AS qty_lost,
    RTRIM(SH6.H6_DTAPONT) AS appointment_date,
    SH6.R_E_C_N_O_ AS appointment_id
FROM SH6010 SH6 WITH (NOLOCK)
INNER JOIN SH1010 SH1 WITH (NOLOCK)
    ON SH1.H1_FILIAL = SH6.H6_FILIAL
   AND SH1.H1_CODIGO = SH6.H6_RECURSO
   AND SH1.D_E_L_E_T_ = ' '
INNER JOIN SHB010 HB WITH (NOLOCK)
    ON HB.HB_FILIAL = SH6.H6_FILIAL
   AND HB.HB_COD = SH1.H1_CTRAB
   AND HB.D_E_L_E_T_ = ' '
LEFT JOIN SB1010 SB1 WITH (NOLOCK)
    ON SB1.B1_COD = SH6.H6_PRODUTO
   AND SB1.D_E_L_E_T_ = ' '
WHERE SH6.D_E_L_E_T_ = ' '
  AND SH6.H6_TIPO = 'P'
  AND SH6.H6_OP <> ''
  AND SH6.H6_RECURSO <> ''
  AND SH6.H6_FILIAL = ?
  AND SH6.H6_DTAPONT >= ?
  AND SH6.H6_DTAPONT < ?
ORDER BY SH6.H6_DTAPONT DESC, SH6.R_E_C_N_O_ DESC
""",
        (BRANCH, DATE_START, DATE_END_EXCL),
    ),
    "summary_by_ct": (
        f"""
SELECT
    RTRIM(SH1.H1_CTRAB) AS work_center,
    RTRIM(HB.HB_NOME) AS work_center_name,
    CASE
        WHEN UPPER(HB.HB_NOME) LIKE '{CT_INSPECAO_LIKE}' THEN 1
        ELSE 0
    END AS is_final_inspection,
    COUNT(*) AS appointment_count,
    SUM(CAST(SH6.H6_QTDPROD AS FLOAT)) AS qty_produced,
    SUM(CAST(SH6.H6_QTDPERD AS FLOAT)) AS qty_lost,
    COUNT(DISTINCT RTRIM(SH6.H6_OP)) AS op_count
FROM SH6010 SH6 WITH (NOLOCK)
INNER JOIN SH1010 SH1 WITH (NOLOCK)
    ON SH1.H1_FILIAL = SH6.H6_FILIAL
   AND SH1.H1_CODIGO = SH6.H6_RECURSO
   AND SH1.D_E_L_E_T_ = ' '
INNER JOIN SHB010 HB WITH (NOLOCK)
    ON HB.HB_FILIAL = SH6.H6_FILIAL
   AND HB.HB_COD = SH1.H1_CTRAB
   AND HB.D_E_L_E_T_ = ' '
WHERE SH6.D_E_L_E_T_ = ' '
  AND SH6.H6_TIPO = 'P'
  AND SH6.H6_OP <> ''
  AND SH6.H6_RECURSO <> ''
  AND SH6.H6_FILIAL = ?
  AND SH6.H6_DTAPONT >= ?
  AND SH6.H6_DTAPONT < ?
GROUP BY SH1.H1_CTRAB, HB.HB_NOME
ORDER BY qty_produced DESC
""",
        (BRANCH, DATE_START, DATE_END_EXCL),
    ),
    "series_by_day": (
        """
SELECT
    RTRIM(SH6.H6_DTAPONT) AS appointment_date,
    COUNT(*) AS appointment_count,
    SUM(CAST(SH6.H6_QTDPROD AS FLOAT)) AS qty_produced,
    SUM(CAST(SH6.H6_QTDPERD AS FLOAT)) AS qty_lost
FROM SH6010 SH6 WITH (NOLOCK)
INNER JOIN SH1010 SH1 WITH (NOLOCK)
    ON SH1.H1_FILIAL = SH6.H6_FILIAL
   AND SH1.H1_CODIGO = SH6.H6_RECURSO
   AND SH1.D_E_L_E_T_ = ' '
WHERE SH6.D_E_L_E_T_ = ' '
  AND SH6.H6_TIPO = 'P'
  AND SH6.H6_OP <> ''
  AND SH6.H6_RECURSO <> ''
  AND SH6.H6_FILIAL = ?
  AND SH6.H6_DTAPONT >= ?
  AND SH6.H6_DTAPONT < ?
GROUP BY SH6.H6_DTAPONT
ORDER BY SH6.H6_DTAPONT
""",
        (BRANCH, DATE_START, DATE_END_EXCL),
    ),
    "drilldown_by_op": (
        """
SELECT TOP 30
    RTRIM(SH6.H6_OP) AS production_order,
    RTRIM(SH6.H6_PRODUTO) AS product,
    COUNT(*) AS appointment_count,
    COUNT(DISTINCT RTRIM(SH1.H1_CTRAB)) AS work_center_count,
    SUM(CAST(SH6.H6_QTDPROD AS FLOAT)) AS qty_produced,
    SUM(CAST(SH6.H6_QTDPERD AS FLOAT)) AS qty_lost,
    MIN(RTRIM(SH6.H6_DTAPONT)) AS first_date,
    MAX(RTRIM(SH6.H6_DTAPONT)) AS last_date
FROM SH6010 SH6 WITH (NOLOCK)
INNER JOIN SH1010 SH1 WITH (NOLOCK)
    ON SH1.H1_FILIAL = SH6.H6_FILIAL
   AND SH1.H1_CODIGO = SH6.H6_RECURSO
   AND SH1.D_E_L_E_T_ = ' '
WHERE SH6.D_E_L_E_T_ = ' '
  AND SH6.H6_TIPO = 'P'
  AND SH6.H6_OP <> ''
  AND SH6.H6_RECURSO <> ''
  AND SH6.H6_FILIAL = ?
  AND SH6.H6_DTAPONT >= ?
  AND SH6.H6_DTAPONT < ?
GROUP BY SH6.H6_OP, SH6.H6_PRODUTO
ORDER BY qty_produced DESC
""",
        (BRANCH, DATE_START, DATE_END_EXCL),
    ),
    "filter_one_ct": (
        """
SELECT
    RTRIM(SH1.H1_CTRAB) AS work_center,
    COUNT(*) AS appointment_count,
    SUM(CAST(SH6.H6_QTDPROD AS FLOAT)) AS qty_produced
FROM SH6010 SH6 WITH (NOLOCK)
INNER JOIN SH1010 SH1 WITH (NOLOCK)
    ON SH1.H1_FILIAL = SH6.H6_FILIAL
   AND SH1.H1_CODIGO = SH6.H6_RECURSO
   AND SH1.D_E_L_E_T_ = ' '
WHERE SH6.D_E_L_E_T_ = ' '
  AND SH6.H6_TIPO = 'P'
  AND SH6.H6_OP <> ''
  AND SH6.H6_RECURSO <> ''
  AND SH6.H6_FILIAL = ?
  AND SH6.H6_DTAPONT >= ?
  AND SH6.H6_DTAPONT < ?
  AND SH1.H1_CTRAB = ?
GROUP BY SH1.H1_CTRAB
""",
        # work_center preenchido em main após catalog
        (BRANCH, DATE_START, DATE_END_EXCL, "__CT__"),
    ),
    "sh6_without_resource_ct": (
        """
SELECT
    COUNT(*) AS appointments_missing_ct_link
FROM SH6010 SH6 WITH (NOLOCK)
LEFT JOIN SH1010 SH1 WITH (NOLOCK)
    ON SH1.H1_FILIAL = SH6.H6_FILIAL
   AND SH1.H1_CODIGO = SH6.H6_RECURSO
   AND SH1.D_E_L_E_T_ = ' '
WHERE SH6.D_E_L_E_T_ = ' '
  AND SH6.H6_TIPO = 'P'
  AND SH6.H6_FILIAL = ?
  AND SH6.H6_DTAPONT >= ?
  AND SH6.H6_DTAPONT < ?
  AND (SH6.H6_RECURSO = '' OR SH1.H1_CODIGO IS NULL OR NULLIF(RTRIM(SH1.H1_CTRAB), '') IS NULL)
""",
        (BRANCH, DATE_START, DATE_END_EXCL),
    ),
    "produced_qty_inspection_ct": (
        f"""
SELECT
    RTRIM(SH1.H1_CTRAB) AS work_center,
    RTRIM(HB.HB_NOME) AS work_center_name,
    SUM(CAST(SH6.H6_QTDPROD AS FLOAT)) AS qty_produced,
    COUNT(*) AS appointment_count
FROM SH6010 SH6 WITH (NOLOCK)
INNER JOIN SH1010 SH1 WITH (NOLOCK)
    ON SH1.H1_FILIAL = SH6.H6_FILIAL
   AND SH1.H1_CODIGO = SH6.H6_RECURSO
   AND SH1.D_E_L_E_T_ = ' '
INNER JOIN SHB010 HB WITH (NOLOCK)
    ON HB.HB_FILIAL = SH6.H6_FILIAL
   AND HB.HB_COD = SH1.H1_CTRAB
   AND HB.D_E_L_E_T_ = ' '
   AND UPPER(HB.HB_NOME) LIKE '{CT_INSPECAO_LIKE}'
INNER JOIN SB1010 SB1 WITH (NOLOCK)
    ON SB1.B1_COD = SH6.H6_PRODUTO
   AND SB1.D_E_L_E_T_ = ' '
   AND SB1.B1_TIPO IN ('PA', 'PI')
WHERE SH6.D_E_L_E_T_ = ' '
  AND SH6.H6_TIPO = 'P'
  AND SH6.H6_OP <> ''
  AND SH6.H6_PRODUTO <> ''
  AND SH6.H6_RECURSO <> ''
  AND SH6.H6_FILIAL = ?
  AND SH6.H6_DTAPONT >= ?
  AND SH6.H6_DTAPONT < ?
GROUP BY SH1.H1_CTRAB, HB.HB_NOME
""",
        (BRANCH, DATE_START, DATE_END_EXCL),
    ),
}


def main() -> None:
    names = sys.argv[1:] if len(sys.argv) > 1 else list(PROBES)
    conn = connect()
    cur = conn.cursor()
    results: list[dict[str, Any]] = []

    # Resolve CT de maior volume para filter_one_ct
    sample_ct = "CT-01"
    try:
        summary = run_probe(cur, "summary_by_ct_prefetch", PROBES["summary_by_ct"][0], PROBES["summary_by_ct"][1])
        if summary["sample"]:
            sample_ct = str(summary["sample"][0].get("work_center") or sample_ct)
        results.append(summary)
    except Exception as exc:  # noqa: BLE001
        print("prefetch summary failed:", exc, flush=True)

    for name in names:
        if name == "summary_by_ct" and any(r.get("name") == "summary_by_ct_prefetch" for r in results):
            # já rodou no prefetch
            pref = next(r for r in results if r["name"] == "summary_by_ct_prefetch")
            results.append({**pref, "name": "summary_by_ct"})
            continue
        sql, params = PROBES[name]
        if name == "filter_one_ct":
            params = (BRANCH, DATE_START, DATE_END_EXCL, sample_ct)
            print(f"(filter_one_ct using work_center={sample_ct})", flush=True)
        try:
            results.append(run_probe(cur, name, sql, params))
        except Exception as exc:  # noqa: BLE001
            print(f"ERR {name}: {exc}", flush=True)
            results.append({"name": name, "error": str(exc), "rows": 0, "elapsed_ms": None})

    conn.close()

    print("\n" + "=" * 60, flush=True)
    print("SUMMARY", flush=True)
    ok = 0
    for r in results:
        if r.get("name") == "summary_by_ct_prefetch":
            continue
        status = "OK" if not r.get("error") and (r.get("rows") or 0) >= 0 and r.get("elapsed_ms") is not None else "FAIL"
        if status == "OK":
            ok += 1
        print(
            f"  {status} {r.get('name')}: rows={r.get('rows')} ms={r.get('elapsed_ms')} {r.get('error') or ''}",
            flush=True,
        )
    printable = [r for r in results if r.get("name") != "summary_by_ct_prefetch"]
    print(f"checks_ok={ok}/{len(printable)} sample_ct={sample_ct}", flush=True)

    out_path = os.environ.get("PROBE_JSON_OUT")
    if out_path:
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "period": {"date_start": DATE_START, "date_end_exclusive": DATE_END_EXCL},
                    "branch": BRANCH,
                    "sample_ct": sample_ct,
                    "results": printable,
                },
                fh,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        print(f"wrote {out_path}", flush=True)


if __name__ == "__main__":
    main()
