#!/usr/bin/env python3
"""Fase 0.1 — probe somente leitura SC1/SC7/SD1 (Solicitações de Compra).

Executa SELECT controlados no TOTVS via pyodbc. Não altera dados.
Uso (container delpi-api-delpi ou host com ODBC + env):
  set -a && source infra/.env && set +a
  python api-delpi/scripts/sql/purchase_requests_totvs_probe.py [--branch 01]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from typing import Any

import pyodbc

BRANCH_DEFAULT = os.environ.get("PROBE_BRANCH", "01")
ANCHOR_SC = "164708"
ANCHOR_PC = "041446"

# Keywords for SX3 / column discovery (requester, CC, approval, buyer, etc.)
SX3_KEYWORDS = (
    "SOLIC", "REQUIS", "USU", "USER", "USR", "EMISS", "RESPON",
    "CC", "CUSTO", "CONTA", "RATEIO", "DEPT", "SETOR", "AREA",
    "APROV", "ALCADA", "LIBER", "BLOQ", "STAT", "SITU", "WORK",
    "COMPR", "COTAD", "GRUPO", "PEDIDO", "QUJE", "RESID", "CANCEL",
    "ORIG", "ITEM", "FORNE", "DATPRF", "EMISSAO",
)

CANDIDATE_SUBSTRINGS = SX3_KEYWORDS


def connect() -> pyodbc.Connection:
    for key in ("TOTVS_DB_HOST", "TOTVS_DB_DATABASE", "TOTVS_DB_USER", "TOTVS_DB_PASSWORD"):
        if not os.environ.get(key):
            raise SystemExit(
                f"FASE 0.1 BLOQUEADA: variável {key} ausente. "
                "Carregue infra/.env antes de executar."
            )
    host = os.environ["TOTVS_DB_HOST"]
    port = os.environ.get("TOTVS_DB_PORT", "1433")
    db = os.environ["TOTVS_DB_DATABASE"]
    user = os.environ["TOTVS_DB_USER"]
    pwd = os.environ["TOTVS_DB_PASSWORD"]
    print(f"host={host} port={port} db={db} user={user}", flush=True)
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
            print(f"connected with {driver}", flush=True)
            return conn
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            print(f"fail {driver}: {type(exc).__name__}: {exc}", flush=True)
    raise SystemExit(f"FASE 0.1 BLOQUEADA POR INDISPONIBILIDADE DO TOTVS: {last_err}")


def mask_value(val: Any, kind: str = "generic") -> str:
    if val is None:
        return ""
    s = str(val).strip()
    if not s:
        return ""
    if kind == "email" and "@" in s:
        local, _, domain = s.partition("@")
        return f"{local[:2]}***@{domain[:3]}***"
    if kind == "name" and len(s) > 4:
        return s[:3] + "***" + s[-1]
    if len(s) <= 4:
        return s[0] + "***"
    return s[:2] + "***" + s[-2:]


def rows_as_dicts(cur: pyodbc.Cursor, mask_cols: set[str] | None = None) -> list[dict[str, Any]]:
    mask_cols = mask_cols or set()
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
            if col in mask_cols and val:
                kind = "email" if "MAIL" in col.upper() or "EMAIL" in col.upper() else "name"
                val = mask_value(val, kind)
            item[col] = val
        out.append(item)
    return out


def run_probe(
    cur: pyodbc.Cursor,
    name: str,
    sql: str,
    params: tuple[Any, ...] = (),
    mask_cols: set[str] | None = None,
    max_print: int = 30,
) -> dict[str, Any]:
    print(f"\n{'=' * 70}\nPROBE: {name}\n{'=' * 70}", flush=True)
    t0 = time.perf_counter()
    try:
        cur.execute(sql, params)
        data = rows_as_dicts(cur, mask_cols)
    except Exception as exc:  # noqa: BLE001
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
        print(f"ERR {type(exc).__name__}: {exc}", flush=True)
        return {"name": name, "error": str(exc), "elapsed_ms": elapsed_ms}
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
    print(f"rows={len(data)} elapsed_ms={elapsed_ms}", flush=True)
    for row in data[:max_print]:
        print(json.dumps(row, ensure_ascii=False, default=str), flush=True)
    if len(data) > max_print:
        print(f"... ({len(data) - max_print} more)", flush=True)
    return {"name": name, "rows": len(data), "elapsed_ms": elapsed_ms, "sample": data[:15]}


def discover_sx3_table(cur: pyodbc.Cursor) -> str | None:
    run_probe(
        cur,
        "sx3_table_catalog",
        """
SELECT TOP 10 name
FROM sys.tables WITH (NOLOCK)
WHERE name LIKE 'SX3%'
ORDER BY name
""",
    )
    cur.execute(
        """
SELECT TOP 1 name
FROM sys.tables WITH (NOLOCK)
WHERE name LIKE 'SX3%'
ORDER BY name
"""
    )
    row = cur.fetchone()
    # Prefer empresa suffix table (SX3010) over base SX3 when both exist.
    cur.execute(
        """
SELECT name FROM sys.tables WITH (NOLOCK)
WHERE name LIKE 'SX3%010' ORDER BY name
"""
    )
    suffixed = [str(r[0]).strip() for r in cur.fetchall()]
    if suffixed:
        return suffixed[0]
    return str(row[0]).strip() if row else None


def sx3_dictionary(cur: pyodbc.Cursor, sx3_table: str, arquivo: str, label: str) -> None:
    like_clauses = " OR ".join(
        f"UPPER(RTRIM(X3_CAMPO)) LIKE '%{kw}%' OR UPPER(RTRIM(X3_TITULO)) LIKE '%{kw}%'"
        f" OR UPPER(RTRIM(X3_DESCRIC)) LIKE '%{kw}%'"
        for kw in SX3_KEYWORDS
    )
    run_probe(
        cur,
        f"sx3_{arquivo}_keywords",
        f"""
SELECT
    RTRIM(X3_CAMPO) AS campo,
    RTRIM(X3_TITULO) AS titulo,
    RTRIM(X3_DESCRIC) AS descricao,
    RTRIM(X3_TIPO) AS tipo,
    X3_TAMANHO AS tamanho,
    X3_DECIMAL AS decimais,
    RTRIM(X3_USADO) AS usado
FROM {sx3_table} WITH (NOLOCK)
WHERE X3_ARQUIVO = ?
  AND ({like_clauses})
ORDER BY X3_CAMPO
""",
        (arquivo,),
        max_print=80,
    )
    run_probe(
        cur,
        f"sx3_{arquivo}_full_count",
        f"""
SELECT COUNT(*) AS total_campos
FROM {sx3_table} WITH (NOLOCK)
WHERE X3_ARQUIVO = ?
""",
        (arquivo,),
    )


def list_table_columns(cur: pyodbc.Cursor, table: str) -> list[str]:
    cur.execute(
        """
SELECT c.name
FROM sys.columns c
INNER JOIN sys.tables t ON t.object_id = c.object_id
WHERE t.name = ?
ORDER BY c.column_id
""",
        (table,),
    )
    return [str(r[0]).strip() for r in cur.fetchall()]


def candidate_columns(all_cols: list[str]) -> list[str]:
    out: list[str] = []
    for col in all_cols:
        upper = col.upper()
        if any(s in upper for s in CANDIDATE_SUBSTRINGS):
            out.append(col)
    return sorted(set(out))


def fill_rate_probe(cur: pyodbc.Cursor, table: str, column: str, branch: str, branch_col: str) -> None:
    sql = f"""
SELECT
    COUNT(*) AS n,
    SUM(CASE WHEN NULLIF(LTRIM(RTRIM(CONVERT(VARCHAR(120), {column}))), '') IS NULL THEN 0 ELSE 1 END) AS filled
FROM (
    SELECT TOP (300) {column}
    FROM {table} WITH (NOLOCK)
    WHERE {branch_col} = ?
      AND D_E_L_E_T_ = ' '
    ORDER BY R_E_C_N_O_ DESC
) s
"""
    run_probe(cur, f"fill_{table}_{column}", sql, (branch,))


def main() -> int:
    parser = argparse.ArgumentParser(description="Fase 0.1 probe SC1/SC7/SD1")
    parser.add_argument("--branch", default=BRANCH_DEFAULT, help="Filial TOTVS (default 01)")
    args = parser.parse_args()
    branch = args.branch

    print(f"branch={branch} anchor_sc={ANCHOR_SC} anchor_pc={ANCHOR_PC}", flush=True)

    conn = connect()
    cur = conn.cursor()

    # --- SX3 discovery ---
    sx3 = discover_sx3_table(cur)
    if not sx3:
        print("WARN: SX3 table not found", flush=True)
    else:
        print(f"sx3_table={sx3}", flush=True)
        sx3_dictionary(cur, sx3, "SC1", "SC1010")
        sx3_dictionary(cur, sx3, "SC7", "SC7010")

    # --- Physical columns ---
    sc1_cols = list_table_columns(cur, "SC1010")
    sc7_cols = list_table_columns(cur, "SC7010")
    print(f"\nSC1010 columns={len(sc1_cols)}", flush=True)
    print(f"SC7010 columns={len(sc7_cols)}", flush=True)
    sc1_cands = candidate_columns(sc1_cols)
    sc7_cands = candidate_columns(sc7_cols)
    print(f"SC1010 candidates={sc1_cands}", flush=True)
    print(f"SC7010 candidates={sc7_cands}", flush=True)

    # --- Fill rates for SC1 candidates (subset) ---
    priority_sc1 = [c for c in sc1_cands if any(
        x in c.upper() for x in ("SOLIC", "USU", "USER", "USR", "CC", "CUSTO", "CONTA", "APROV", "LIBER", "BLOQ", "DEPT", "SETOR")
    )]
    for col in priority_sc1[:25]:
        fill_rate_probe(cur, "SC1010", col, branch, "C1_FILIAL")

    priority_sc7 = [c for c in sc7_cands if any(
        x in c.upper() for x in ("COMPR", "USU", "USER", "USR", "COTAD", "GRUPO", "SOLIC", "NUMSC", "SC", "ORIG")
    )]
    for col in priority_sc7[:25]:
        fill_rate_probe(cur, "SC7010", col, branch, "C7_FILIAL")

    # --- Anchor case SC 164708 / PC 041446 ---
    run_probe(
        cur,
        "anchor_sc_lines",
        """
SELECT
    RTRIM(C1_FILIAL) AS filial,
    RTRIM(C1_NUM) AS sc_num,
    RTRIM(C1_ITEM) AS sc_item,
    RTRIM(C1_PRODUTO) AS produto,
    C1_QUANT, C1_QUJE,
    RTRIM(C1_PEDIDO) AS pedido,
    RTRIM(C1_RESIDUO) AS residuo,
    RTRIM(C1_EMISSAO) AS emissao,
    RTRIM(C1_DATPRF) AS datprf,
    RTRIM(C1_FORNECE) AS fornece,
    RTRIM(C1_LOJA) AS loja,
    RTRIM(C1_SOLICIT) AS c1_solicit,
    RTRIM(C1_USER) AS c1_user,
    RTRIM(C1_CC) AS c1_cc,
    RTRIM(C1_APROV) AS c1_aprov,
    RTRIM(C1_NOMAPRO) AS c1_nomaprov,
    RTRIM(C1_XGRPAPR) AS c1_xgrpapr,
    RTRIM(C1_OBS) AS c1_obs,
    D_E_L_E_T_ AS deleted
FROM SC1010 WITH (NOLOCK)
WHERE C1_NUM = ?
  AND D_E_L_E_T_ = ' '
ORDER BY C1_ITEM
""",
        (ANCHOR_SC,),
        mask_cols={"c1_obs"},
    )

    run_probe(
        cur,
        "anchor_pc_lines",
        """
SELECT
    RTRIM(C7_FILIAL) AS filial,
    RTRIM(C7_NUM) AS pc_num,
    RTRIM(C7_ITEM) AS pc_item,
    RTRIM(C7_PRODUTO) AS produto,
    C7_QUANT, C7_QUJE,
    RTRIM(C7_RESIDUO) AS residuo,
    RTRIM(C7_EMISSAO) AS emissao,
    RTRIM(C7_DATPRF) AS datprf,
    RTRIM(C7_FORNECE) AS fornece,
    RTRIM(C7_LOJA) AS loja,
    RTRIM(C7_COMPRA) AS c7_compra,
    RTRIM(C7_USER) AS c7_user,
    RTRIM(C7_NUMSC) AS c7_numsc,
    RTRIM(C7_ITEMSC) AS c7_itemsc,
    RTRIM(C7_SOLICIT) AS c7_solicit,
    D_E_L_E_T_ AS deleted
FROM SC7010 WITH (NOLOCK)
WHERE C7_NUM = ?
  AND D_E_L_E_T_ = ' '
ORDER BY C7_ITEM
""",
        (ANCHOR_PC,),
    )

    # Dynamic anchor — only columns that exist
    sc7_origin_cols = [c for c in sc7_cols if re.search(r"SC|SOLIC|ORIG|NUMSC", c, re.I)]
    if sc7_origin_cols:
        sel = ", ".join(f"RTRIM({c}) AS {c.lower()}" for c in sc7_origin_cols[:12])
        run_probe(
            cur,
            "anchor_pc_origin_fields",
            f"""
SELECT TOP 20 {sel}
FROM SC7010 WITH (NOLOCK)
WHERE C7_NUM = ? AND D_E_L_E_T_ = ' '
""",
            (ANCHOR_PC,),
        )

    run_probe(
        cur,
        "anchor_sd1_docs",
        """
SELECT
    RTRIM(D1_FILIAL) AS filial,
    RTRIM(D1_DOC) AS doc,
    RTRIM(D1_SERIE) AS serie,
    RTRIM(D1_ITEM) AS d1_item,
    RTRIM(D1_PEDIDO) AS pedido,
    RTRIM(D1_ITEMPC) AS item_pc,
    RTRIM(D1_COD) AS produto,
    D1_QUANT,
    RTRIM(D1_FORNECE) AS fornece,
    RTRIM(D1_LOJA) AS loja,
    RTRIM(D1_EMISSAO) AS emissao,
    RTRIM(D1_DTDIGIT) AS dtdigit,
    D_E_L_E_T_ AS deleted
FROM SD1010 WITH (NOLOCK)
WHERE D1_PEDIDO = ?
  AND D_E_L_E_T_ = ' '
ORDER BY D1_DOC, D1_ITEM
""",
        (ANCHOR_PC,),
    )

    # --- Requester validation (try common fields if exist) ---
    requester_fields = [c for c in sc1_cols if re.search(r"SOLIC|REQUIS|USU|USER|USR|EMISS", c, re.I)]
    for fld in requester_fields[:8]:
        run_probe(
            cur,
            f"requester_sample_{fld}",
            f"""
SELECT TOP 10
    RTRIM(C1_NUM) AS sc_num,
    RTRIM({fld}) AS code,
    COUNT(*) AS cnt
FROM SC1010 WITH (NOLOCK)
WHERE C1_FILIAL = ?
  AND D_E_L_E_T_ = ' '
  AND NULLIF(RTRIM({fld}), '') IS NOT NULL
GROUP BY RTRIM(C1_NUM), RTRIM({fld})
ORDER BY cnt DESC
""",
            (branch,),
        )

    # SYS_USR join if C1_SOLICIT or similar filled
    for fld in ("C1_SOLICIT", "C1_USER", "C1_SOLIC"):
        if fld not in sc1_cols:
            continue
        run_probe(
            cur,
            f"sys_usr_join_{fld}",
            f"""
SELECT TOP 15
    RTRIM(SC.{fld}) AS protheus_code,
    RTRIM(U.USR_ID) AS usr_id,
    RTRIM(U.USR_CODIGO) AS usr_codigo,
    RTRIM(U.USR_NOME) AS usr_nome,
    RTRIM(U.USR_EMAIL) AS usr_email
FROM (
    SELECT DISTINCT TOP 50 RTRIM({fld}) AS {fld}
    FROM SC1010 WITH (NOLOCK)
    WHERE C1_FILIAL = ? AND D_E_L_E_T_ = ' ' AND NULLIF(RTRIM({fld}), '') IS NOT NULL
) SC
LEFT JOIN SYS_USR U WITH (NOLOCK)
    ON RTRIM(U.USR_ID) = SC.{fld}
    OR RTRIM(U.USR_CODIGO) = SC.{fld}
WHERE SC.{fld} <> ''
""",
            (branch,),
            mask_cols={"usr_nome", "usr_email", "usr_login"},
        )

    # --- Cost center ---
    cc_fields = [c for c in sc1_cols if re.search(r"^C1_.*CC|CUSTO|CONTA|RATEIO|DEPT", c, re.I)]
    for fld in cc_fields[:10]:
        run_probe(
            cur,
            f"cc_sample_{fld}",
            f"""
SELECT TOP 15
    RTRIM({fld}) AS cc_code,
    COUNT(*) AS cnt
FROM SC1010 WITH (NOLOCK)
WHERE C1_FILIAL = ? AND D_E_L_E_T_ = ' '
  AND NULLIF(RTRIM({fld}), '') IS NOT NULL
GROUP BY RTRIM({fld})
ORDER BY cnt DESC
""",
            (branch,),
        )

    # vw_fin_despesas_centro_custo overlap
    run_probe(
        cur,
        "cc_catalog_overlap",
        """
SELECT TOP 1 1 AS view_exists
FROM sys.views WITH (NOLOCK)
WHERE name = 'vw_fin_despesas_centro_custo'
""",
    )
    if "C1_CC" in sc1_cols:
        run_probe(
            cur,
            "cc_sc_vs_catalog",
            """
SELECT
    COUNT(DISTINCT RTRIM(C1_CC)) AS sc_distinct_cc,
    SUM(CASE WHEN V.cc IS NOT NULL THEN 1 ELSE 0 END) AS matched_rows,
    COUNT(*) AS total_rows
FROM SC1010 SC WITH (NOLOCK)
LEFT JOIN (
    SELECT DISTINCT RTRIM(centro_custo_codigo) AS cc
    FROM dbo.vw_fin_despesas_centro_custo WITH (NOLOCK)
) V ON V.cc = RTRIM(SC.C1_CC)
WHERE SC.C1_FILIAL = ?
  AND SC.D_E_L_E_T_ = ' '
  AND NULLIF(RTRIM(SC.C1_CC), '') IS NOT NULL
""",
            (branch,),
        )

    # --- Buyer SC7 ---
    buyer_fields = [c for c in sc7_cols if re.search(r"COMPR|COTAD|USU|USER|USR", c, re.I)]
    for fld in buyer_fields[:8]:
        run_probe(
            cur,
            f"buyer_sample_{fld}",
            f"""
SELECT TOP 10
    RTRIM({fld}) AS code,
    COUNT(*) AS cnt
FROM SC7010 WITH (NOLOCK)
WHERE C7_FILIAL = ? AND D_E_L_E_T_ = ' '
  AND NULLIF(RTRIM({fld}), '') IS NOT NULL
GROUP BY RTRIM({fld})
ORDER BY cnt DESC
""",
            (branch,),
        )

    # --- Approval fields SC1 ---
    approval_fields = [c for c in sc1_cols if re.search(r"APROV|LIBER|BLOQ|ALCAD|STAT|SITU", c, re.I)]
    for fld in approval_fields[:12]:
        run_probe(
            cur,
            f"approval_distinct_{fld}",
            f"""
SELECT TOP 20
    RTRIM({fld}) AS val,
    COUNT(*) AS cnt
FROM SC1010 WITH (NOLOCK)
WHERE C1_FILIAL = ? AND D_E_L_E_T_ = ' '
GROUP BY RTRIM({fld})
ORDER BY cnt DESC
""",
            (branch,),
        )

    # --- Cardinality SC -> PC ---
    run_probe(
        cur,
        "cardinality_sc_item_to_pc",
        """
SELECT TOP 20
    RTRIM(C1_FILIAL) AS filial,
    RTRIM(C1_NUM) AS sc_num,
    RTRIM(C1_ITEM) AS sc_item,
    COUNT(DISTINCT RTRIM(C1_PEDIDO)) AS distinct_pcs,
    STRING_AGG(RTRIM(C1_PEDIDO), ',') AS pcs
FROM SC1010 WITH (NOLOCK)
WHERE C1_FILIAL = ?
  AND D_E_L_E_T_ = ' '
  AND NULLIF(RTRIM(C1_PEDIDO), '') IS NOT NULL
GROUP BY RTRIM(C1_FILIAL), RTRIM(C1_NUM), RTRIM(C1_ITEM)
HAVING COUNT(DISTINCT RTRIM(C1_PEDIDO)) > 1
ORDER BY distinct_pcs DESC
""",
        (branch,),
    )

    run_probe(
        cur,
        "cardinality_pc_to_sc_via_c7_numsc",
        """
SELECT TOP 20
    RTRIM(C7_NUM) AS pc_num,
    COUNT(DISTINCT RTRIM(C7_NUMSC)) AS distinct_scs
FROM SC7010 WITH (NOLOCK)
WHERE C7_FILIAL = ?
  AND D_E_L_E_T_ = ' '
  AND NULLIF(RTRIM(C7_NUMSC), '') IS NOT NULL
GROUP BY RTRIM(C7_NUM)
HAVING COUNT(DISTINCT RTRIM(C7_NUMSC)) > 1
ORDER BY distinct_scs DESC
""",
        (branch,),
    )

    run_probe(
        cur,
        "cardinality_c1_pedido_vs_c7",
        """
SELECT TOP 15
    RTRIM(SC.C1_NUM) AS sc_num,
    RTRIM(SC.C1_ITEM) AS sc_item,
    RTRIM(SC.C1_PEDIDO) AS c1_pedido,
    RTRIM(C7.C7_NUM) AS c7_num,
    RTRIM(C7.C7_ITEM) AS c7_item,
    RTRIM(SC.C1_PRODUTO) AS sc_prod,
    RTRIM(C7.C7_PRODUTO) AS c7_prod,
    RTRIM(C7.C7_NUMSC) AS c7_numsc,
    RTRIM(C7.C7_ITEMSC) AS c7_itemsc
FROM SC1010 SC WITH (NOLOCK)
INNER JOIN SC7010 C7 WITH (NOLOCK)
    ON RTRIM(C7.C7_NUM) = RTRIM(SC.C1_PEDIDO)
   AND C7.D_E_L_E_T_ = ' '
WHERE SC.C1_FILIAL = ?
  AND SC.D_E_L_E_T_ = ' '
  AND NULLIF(RTRIM(SC.C1_PEDIDO), '') IS NOT NULL
  AND RTRIM(SC.C1_PRODUTO) <> RTRIM(C7.C7_PRODUTO)
ORDER BY SC.R_E_C_N_O_ DESC
""",
        (branch,),
    )

    # --- PC -> SD1 cardinality ---
    run_probe(
        cur,
        "cardinality_pc_multi_nf",
        """
SELECT TOP 15
    RTRIM(D1_PEDIDO) AS pedido,
    RTRIM(D1_FORNECE) AS fornece,
    RTRIM(D1_LOJA) AS loja,
    RTRIM(D1_COD) AS produto,
    COUNT(DISTINCT RTRIM(D1_DOC)) AS distinct_docs
FROM SD1010 WITH (NOLOCK)
WHERE D1_FILIAL = ?
  AND D_E_L_E_T_ = ' '
  AND NULLIF(RTRIM(D1_PEDIDO), '') IS NOT NULL
GROUP BY RTRIM(D1_PEDIDO), RTRIM(D1_FORNECE), RTRIM(D1_LOJA), RTRIM(D1_COD)
HAVING COUNT(DISTINCT RTRIM(D1_DOC)) > 1
ORDER BY distinct_docs DESC
""",
        (branch,),
    )

    run_probe(
        cur,
        "d1_itempc_vs_c7_item",
        """
SELECT TOP 15
    RTRIM(D1_PEDIDO) AS pedido,
    RTRIM(D1_ITEMPC) AS d1_itempc,
    RTRIM(C7.C7_ITEM) AS c7_item,
    RTRIM(D1_COD) AS produto,
    D1_QUANT
FROM SD1010 D1 WITH (NOLOCK)
INNER JOIN SC7010 C7 WITH (NOLOCK)
    ON RTRIM(C7.C7_NUM) = RTRIM(D1.D1_PEDIDO)
   AND RTRIM(C7.C7_PRODUTO) = RTRIM(D1.D1_COD)
   AND C7.D_E_L_E_T_ = ' '
WHERE D1.D1_FILIAL = ?
  AND D1.D_E_L_E_T_ = ' '
  AND NULLIF(RTRIM(D1.D1_PEDIDO), '') IS NOT NULL
  AND NULLIF(RTRIM(D1.D1_ITEMPC), '') IS NOT NULL
  AND RTRIM(D1.D1_ITEMPC) <> RTRIM(C7.C7_ITEM)
ORDER BY D1.R_E_C_N_O_ DESC
""",
        (branch,),
    )

    # --- Partial receipts C7_QUJE vs SUM(D1_QUANT) ---
    run_probe(
        cur,
        "partial_receipt_c7_vs_sd1",
        """
SELECT TOP 25
    RTRIM(C7.C7_NUM) AS pc_num,
    RTRIM(C7.C7_ITEM) AS c7_item,
    RTRIM(C7.C7_PRODUTO) AS produto,
    C7.C7_QUANT,
    C7.C7_QUJE,
    COALESCE(SUM(D1.D1_QUANT), 0) AS sum_d1_quant,
    ABS(C7.C7_QUJE - COALESCE(SUM(D1.D1_QUANT), 0)) AS diff
FROM SC7010 C7 WITH (NOLOCK)
LEFT JOIN SD1010 D1 WITH (NOLOCK)
    ON RTRIM(D1.D1_PEDIDO) = RTRIM(C7.C7_NUM)
   AND RTRIM(D1.D1_FORNECE) = RTRIM(C7.C7_FORNECE)
   AND RTRIM(D1.D1_LOJA) = RTRIM(C7.C7_LOJA)
   AND RTRIM(D1.D1_COD) = RTRIM(C7.C7_PRODUTO)
   AND D1.D_E_L_E_T_ = ' '
WHERE C7.C7_FILIAL = ?
  AND C7.D_E_L_E_T_ = ' '
  AND C7.C7_QUJE > 0
  AND C7.C7_QUJE < C7.C7_QUANT
GROUP BY
    RTRIM(C7.C7_NUM), RTRIM(C7.C7_ITEM), RTRIM(C7.C7_PRODUTO),
    C7.C7_QUANT, C7.C7_QUJE
ORDER BY diff DESC
""",
        (branch,),
    )

    run_probe(
        cur,
        "receipt_match_rate",
        """
SELECT
    COUNT(*) AS sample_n,
    SUM(CASE WHEN ABS(c7_quje - sum_d1) < 0.001 THEN 1 ELSE 0 END) AS exact_match,
    SUM(CASE WHEN ABS(c7_quje - sum_d1) >= 0.001 THEN 1 ELSE 0 END) AS mismatch
FROM (
    SELECT TOP 200
        C7.C7_QUJE AS c7_quje,
        COALESCE(SUM(D1.D1_QUANT), 0) AS sum_d1
    FROM SC7010 C7 WITH (NOLOCK)
    LEFT JOIN SD1010 D1 WITH (NOLOCK)
        ON RTRIM(D1.D1_PEDIDO) = RTRIM(C7.C7_NUM)
       AND RTRIM(D1.D1_FORNECE) = RTRIM(C7.C7_FORNECE)
       AND RTRIM(D1.D1_LOJA) = RTRIM(C7.C7_LOJA)
       AND RTRIM(D1.D1_COD) = RTRIM(C7.C7_PRODUTO)
       AND RTRIM(D1.D1_ITEMPC) = RTRIM(C7.C7_ITEM)
       AND D1.D_E_L_E_T_ = ' '
    WHERE C7.C7_FILIAL = ?
      AND C7.D_E_L_E_T_ = ' '
      AND C7.C7_QUJE > 0
    GROUP BY C7.R_E_C_N_O_, C7.C7_QUJE, C7.C7_NUM, C7.C7_ITEM
) x
""",
        (branch,),
    )

    # --- Date comparison ---
    run_probe(
        cur,
        "date_fields_anchor",
        """
SELECT
    RTRIM(SC.C1_NUM) AS sc,
    RTRIM(SC.C1_EMISSAO) AS c1_emissao,
    RTRIM(SC.C1_DATPRF) AS c1_datprf,
    RTRIM(C7.C7_EMISSAO) AS c7_emissao,
    RTRIM(C7.C7_DATPRF) AS c7_datprf,
    MIN(RTRIM(D1.D1_EMISSAO)) AS min_d1_emissao,
    MIN(RTRIM(D1.D1_DTDIGIT)) AS min_d1_dtdigit,
    MAX(RTRIM(D1.D1_DTDIGIT)) AS max_d1_dtdigit
FROM SC1010 SC WITH (NOLOCK)
LEFT JOIN SC7010 C7 WITH (NOLOCK)
    ON RTRIM(C7.C7_NUM) = RTRIM(SC.C1_PEDIDO) AND C7.D_E_L_E_T_ = ' '
LEFT JOIN SD1010 D1 WITH (NOLOCK)
    ON RTRIM(D1.D1_PEDIDO) = RTRIM(C7.C7_NUM)
   AND RTRIM(D1.D1_FORNECE) = RTRIM(C7.C7_FORNECE)
   AND RTRIM(D1.D1_LOJA) = RTRIM(C7.C7_LOJA)
   AND RTRIM(D1.D1_COD) = RTRIM(C7.C7_PRODUTO)
   AND D1.D_E_L_E_T_ = ' '
WHERE SC.C1_NUM = ?
  AND SC.D_E_L_E_T_ = ' '
GROUP BY RTRIM(SC.C1_NUM), RTRIM(SC.C1_EMISSAO), RTRIM(SC.C1_DATPRF),
         RTRIM(C7.C7_EMISSAO), RTRIM(C7.C7_DATPRF)
""",
        (ANCHOR_SC,),
    )

    run_probe(
        cur,
        "date_prf_mismatch_sample",
        """
SELECT TOP 15
    RTRIM(SC.C1_NUM) AS sc,
    RTRIM(SC.C1_DATPRF) AS c1_datprf,
    RTRIM(C7.C7_DATPRF) AS c7_datprf
FROM SC1010 SC WITH (NOLOCK)
INNER JOIN SC7010 C7 WITH (NOLOCK)
    ON RTRIM(C7.C7_NUM) = RTRIM(SC.C1_PEDIDO)
   AND C7.D_E_L_E_T_ = ' '
WHERE SC.C1_FILIAL = ?
  AND SC.D_E_L_E_T_ = ' '
  AND NULLIF(RTRIM(SC.C1_PEDIDO), '') IS NOT NULL
  AND RTRIM(SC.C1_DATPRF) <> RTRIM(C7.C7_DATPRF)
ORDER BY SC.R_E_C_N_O_ DESC
""",
        (branch,),
    )

    # --- Residue / delete ---
    run_probe(
        cur,
        "residue_vs_delete_sc1",
        """
SELECT
    SUM(CASE WHEN RTRIM(C1_RESIDUO) = 'S' THEN 1 ELSE 0 END) AS residuo_s,
    SUM(CASE WHEN D_E_L_E_T_ <> ' ' THEN 1 ELSE 0 END) AS deleted,
    SUM(CASE WHEN C1_QUANT <= C1_QUJE THEN 1 ELSE 0 END) AS fully_served,
    COUNT(*) AS total
FROM SC1010 WITH (NOLOCK)
WHERE C1_FILIAL = ?
""",
        (branch,),
    )

    # --- Scenarios A-K ---
    scenarios = {
        "A_sc_sem_pedido": """
SELECT TOP 3 RTRIM(C1_NUM) AS id, RTRIM(C1_ITEM) AS item, C1_QUANT, C1_QUJE
FROM SC1010 WITH (NOLOCK)
WHERE C1_FILIAL = ? AND D_E_L_E_T_ = ' ' AND C1_RESIDUO <> 'S'
  AND (NULLIF(RTRIM(C1_PEDIDO), '') IS NULL)
  AND C1_QUANT > C1_QUJE
ORDER BY R_E_C_N_O_ DESC
""",
        "B_sc_integral_pc": """
SELECT TOP 3 RTRIM(C1_NUM) AS id, RTRIM(C1_ITEM) AS item, C1_QUANT, C1_QUJE, RTRIM(C1_PEDIDO) AS pc
FROM SC1010 WITH (NOLOCK)
WHERE C1_FILIAL = ? AND D_E_L_E_T_ = ' ' AND C1_RESIDUO <> 'S'
  AND NULLIF(RTRIM(C1_PEDIDO), '') IS NOT NULL
  AND C1_QUJE >= C1_QUANT
ORDER BY R_E_C_N_O_ DESC
""",
        "C_sc_parcial": """
SELECT TOP 3 RTRIM(C1_NUM) AS id, RTRIM(C1_ITEM) AS item, C1_QUANT, C1_QUJE, RTRIM(C1_PEDIDO) AS pc
FROM SC1010 WITH (NOLOCK)
WHERE C1_FILIAL = ? AND D_E_L_E_T_ = ' ' AND C1_RESIDUO <> 'S'
  AND C1_QUJE > 0 AND C1_QUJE < C1_QUANT
ORDER BY R_E_C_N_O_ DESC
""",
        "D_pc_sem_receb": """
SELECT TOP 3 RTRIM(C7_NUM) AS id, RTRIM(C7_ITEM) AS item, C7_QUANT, C7_QUJE
FROM SC7010 WITH (NOLOCK)
WHERE C7_FILIAL = ? AND D_E_L_E_T_ = ' ' AND C7_RESIDUO <> 'S'
  AND C7_QUJE = 0 AND C7_QUANT > 0
ORDER BY R_E_C_N_O_ DESC
""",
        "E_pc_parcial": """
SELECT TOP 3 RTRIM(C7_NUM) AS id, RTRIM(C7_ITEM) AS item, C7_QUANT, C7_QUJE
FROM SC7010 WITH (NOLOCK)
WHERE C7_FILIAL = ? AND D_E_L_E_T_ = ' ' AND C7_RESIDUO <> 'S'
  AND C7_QUJE > 0 AND C7_QUJE < C7_QUANT
ORDER BY R_E_C_N_O_ DESC
""",
        "F_pc_total": """
SELECT TOP 3 RTRIM(C7_NUM) AS id, RTRIM(C7_ITEM) AS item, C7_QUANT, C7_QUJE
FROM SC7010 WITH (NOLOCK)
WHERE C7_FILIAL = ? AND D_E_L_E_T_ = ' ' AND C7_RESIDUO <> 'S'
  AND C7_QUJE >= C7_QUANT AND C7_QUANT > 0
ORDER BY R_E_C_N_O_ DESC
""",
        "H_sc_multi_item": """
SELECT TOP 5 RTRIM(C1_NUM) AS id, COUNT(*) AS items
FROM SC1010 WITH (NOLOCK)
WHERE C1_FILIAL = ? AND D_E_L_E_T_ = ' '
GROUP BY RTRIM(C1_NUM)
HAVING COUNT(*) > 1
ORDER BY items DESC
""",
        "J_residuo_sc": """
SELECT TOP 3 RTRIM(C1_NUM) AS id, RTRIM(C1_ITEM) AS item, RTRIM(C1_RESIDUO) AS residuo, C1_QUANT, C1_QUJE
FROM SC1010 WITH (NOLOCK)
WHERE C1_FILIAL = ? AND RTRIM(C1_RESIDUO) = 'S'
ORDER BY R_E_C_N_O_ DESC
""",
        "J_residuo_pc": """
SELECT TOP 3 RTRIM(C7_NUM) AS id, RTRIM(C7_ITEM) AS item, RTRIM(C7_RESIDUO) AS residuo, C7_QUANT, C7_QUJE
FROM SC7010 WITH (NOLOCK)
WHERE C7_FILIAL = ? AND RTRIM(C7_RESIDUO) = 'S'
ORDER BY R_E_C_N_O_ DESC
""",
        "K_deleted_sc": """
SELECT TOP 3 RTRIM(C1_NUM) AS id, RTRIM(C1_ITEM) AS item, D_E_L_E_T_ AS deleted
FROM SC1010 WITH (NOLOCK)
WHERE C1_FILIAL = ? AND D_E_L_E_T_ <> ' '
ORDER BY R_E_C_N_O_ DESC
""",
    }
    for name, sql in scenarios.items():
        run_probe(cur, f"scenario_{name}", sql, (branch,))

    # G and I from dedicated cardinality probes above
    run_probe(
        cur,
        "scenario_G_pc_multi_nf",
        """
SELECT TOP 3
    RTRIM(D1_PEDIDO) AS pc,
    COUNT(DISTINCT RTRIM(D1_DOC)) AS docs
FROM SD1010 WITH (NOLOCK)
WHERE D1_FILIAL = ? AND D_E_L_E_T_ = ' '
  AND NULLIF(RTRIM(D1_PEDIDO), '') IS NOT NULL
GROUP BY RTRIM(D1_PEDIDO)
HAVING COUNT(DISTINCT RTRIM(D1_DOC)) > 1
ORDER BY docs DESC
""",
        (branch,),
    )

    run_probe(
        cur,
        "scenario_I_sc_multi_pc",
        """
SELECT TOP 3
    RTRIM(C1_NUM) AS sc,
    COUNT(DISTINCT RTRIM(C1_PEDIDO)) AS pcs
FROM SC1010 WITH (NOLOCK)
WHERE C1_FILIAL = ? AND D_E_L_E_T_ = ' '
  AND NULLIF(RTRIM(C1_PEDIDO), '') IS NOT NULL
GROUP BY RTRIM(C1_NUM)
HAVING COUNT(DISTINCT RTRIM(C1_PEDIDO)) > 1
ORDER BY pcs DESC
""",
        (branch,),
    )

    # --- Product scope (B1_TIPO) ---
    run_probe(
        cur,
        "product_type_scope_sc",
        """
SELECT TOP 15
    RTRIM(B1.B1_TIPO) AS tipo,
    COUNT(*) AS cnt
FROM SC1010 SC WITH (NOLOCK)
INNER JOIN SB1010 B1 WITH (NOLOCK)
    ON B1.B1_COD = SC.C1_PRODUTO AND B1.D_E_L_E_T_ = ' '
WHERE SC.C1_FILIAL = ?
  AND SC.D_E_L_E_T_ = ' '
GROUP BY RTRIM(B1.B1_TIPO)
ORDER BY cnt DESC
""",
        (branch,),
    )

    # --- Workflow tables discovery ---
    run_probe(
        cur,
        "workflow_tables",
        """
SELECT TOP 30 name
FROM sys.tables WITH (NOLOCK)
WHERE name LIKE '%APR%' OR name LIKE '%ALC%' OR name LIKE '%LIB%' OR name LIKE '%WRK%'
ORDER BY name
""",
    )

    conn.close()
    print("\n=== PROBE COMPLETE ===", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"FATAL {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        raise
