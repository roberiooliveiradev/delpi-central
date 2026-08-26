#!/usr/bin/env python3
"""Supplement probes for Fase 0.1 — run after purchase_requests_totvs_probe.py."""
from __future__ import annotations

import json
import os
import sys

import pyodbc


def connect() -> pyodbc.Connection:
    host = os.environ["TOTVS_DB_HOST"]
    port = os.environ.get("TOTVS_DB_PORT", "1433")
    db = os.environ["TOTVS_DB_DATABASE"]
    user = os.environ["TOTVS_DB_USER"]
    pwd = os.environ["TOTVS_DB_PASSWORD"]
    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={host},{port};DATABASE={db};"
        f"UID={user};PWD={pwd};TrustServerCertificate=yes;Encrypt=no;"
    )
    return pyodbc.connect(conn_str, timeout=30)


def run(cur, name: str, sql: str, params: tuple = ()) -> None:
    print(f"\n=== {name} ===", flush=True)
    try:
        cur.execute(sql, params)
        cols = [c[0] for c in cur.description]
        rows = cur.fetchall()
        print(f"rows={len(rows)}", flush=True)
        for r in rows[:25]:
            d = {}
            for i, col in enumerate(cols):
                val = r[i]
                s = str(val).strip() if val is not None else None
                if col.lower() in ("usr_nome", "usr_email") and s and len(s) > 3:
                    s = s[:2] + "***"
                d[col] = s
            print(json.dumps(d, ensure_ascii=False), flush=True)
    except Exception as exc:  # noqa: BLE001
        print(f"ERR {type(exc).__name__}: {exc}", flush=True)


def main() -> int:
    conn = connect()
    cur = conn.cursor()

    run(
        cur,
        "sx3010_sc1_all",
        """
SELECT RTRIM(X3_CAMPO) AS campo, RTRIM(X3_TITULO) AS titulo, RTRIM(X3_DESCRIC) AS descr,
       RTRIM(X3_TIPO) AS tipo, X3_TAMANHO AS tam, X3_DECIMAL AS dec
FROM SX3010 WITH (NOLOCK) WHERE X3_ARQUIVO='SC1' ORDER BY X3_ORDEM, X3_CAMPO
""",
    )
    run(
        cur,
        "sx3010_sc7_keywords",
        """
SELECT RTRIM(X3_CAMPO) AS campo, RTRIM(X3_TITULO) AS titulo, RTRIM(X3_DESCRIC) AS descr
FROM SX3010 WITH (NOLOCK) WHERE X3_ARQUIVO='SC7'
  AND (X3_CAMPO LIKE '%COMPR%' OR X3_CAMPO LIKE '%NUMSC%' OR X3_CAMPO LIKE '%ITEMSC%'
       OR X3_CAMPO LIKE '%USER%' OR X3_CAMPO LIKE '%APROV%' OR X3_CAMPO LIKE '%QUJE%'
       OR X3_CAMPO LIKE '%RESID%' OR X3_TITULO LIKE '%Compr%' OR X3_TITULO LIKE '%Solic%')
ORDER BY X3_CAMPO
""",
    )
    run(
        cur,
        "sys_usr_cols",
        """
SELECT name FROM sys.columns WHERE object_id=OBJECT_ID('SYS_USR') AND name LIKE 'USR_%'
ORDER BY name
""",
    )
    run(
        cur,
        "requester_c1_user_sys_usr",
        """
SELECT TOP 10
  RTRIM(SC.C1_USER) AS c1_user,
  RTRIM(U.USR_ID) AS usr_id,
  RTRIM(U.USR_CODIGO) AS usr_codigo,
  RTRIM(U.USR_NOME) AS usr_nome,
  RTRIM(U.USR_EMAIL) AS usr_email
FROM SC1010 SC WITH (NOLOCK)
LEFT JOIN SYS_USR U WITH (NOLOCK) ON RTRIM(U.USR_ID)=RTRIM(SC.C1_USER)
WHERE SC.C1_FILIAL='01' AND SC.D_E_L_E_T_=' ' AND NULLIF(RTRIM(SC.C1_USER),'') IS NOT NULL
ORDER BY SC.R_E_C_N_O_ DESC
""",
    )
    run(
        cur,
        "solicit_vs_user",
        """
SELECT TOP 10 RTRIM(C1_SOLICIT) AS solicit, RTRIM(C1_USER) AS c1_user, COUNT(*) AS cnt
FROM SC1010 WITH (NOLOCK)
WHERE C1_FILIAL='01' AND D_E_L_E_T_=' '
GROUP BY RTRIM(C1_SOLICIT), RTRIM(C1_USER)
ORDER BY cnt DESC
""",
    )
    run(
        cur,
        "anchor_sc164708",
        """
SELECT RTRIM(C1_FILIAL) AS filial, RTRIM(C1_NUM) AS sc, RTRIM(C1_ITEM) AS item,
  RTRIM(C1_PRODUTO) AS prod, C1_QUANT, C1_QUJE, RTRIM(C1_PEDIDO) AS pedido,
  RTRIM(C1_RESIDUO) AS residuo, RTRIM(C1_EMISSAO) AS emissao, RTRIM(C1_DATPRF) AS datprf,
  RTRIM(C1_SOLICIT) AS solicit, RTRIM(C1_USER) AS c1_user, RTRIM(C1_CC) AS cc,
  RTRIM(C1_CONTA) AS conta, RTRIM(C1_APROV) AS aprov
FROM SC1010 WITH (NOLOCK) WHERE C1_NUM='164708' AND D_E_L_E_T_=' ' ORDER BY C1_ITEM
""",
    )
    run(
        cur,
        "anchor_pc041446",
        """
SELECT RTRIM(C7_FILIAL) AS filial, RTRIM(C7_NUM) AS pc, RTRIM(C7_ITEM) AS item,
  RTRIM(C7_PRODUTO) AS prod, C7_QUANT, C7_QUJE, RTRIM(C7_NUMSC) AS numsc,
  RTRIM(C7_ITEMSC) AS itemsc, RTRIM(C7_FORNECE) AS fornece, RTRIM(C7_LOJA) AS loja,
  RTRIM(C7_EMISSAO) AS emissao, RTRIM(C7_DATPRF) AS datprf, RTRIM(C7_USER) AS c7_user,
  RTRIM(C7_APROV) AS aprov, RTRIM(C7_RESIDUO) AS residuo
FROM SC7010 WITH (NOLOCK) WHERE C7_NUM='041446' AND D_E_L_E_T_=' ' ORDER BY C7_ITEM
""",
    )
    run(
        cur,
        "cc_overlap",
        """
SELECT COUNT(DISTINCT RTRIM(SC.C1_CC)) AS sc_distinct,
  SUM(CASE WHEN V.cc IS NOT NULL THEN 1 ELSE 0 END) AS matched,
  COUNT(*) AS total,
  CAST(100.0*SUM(CASE WHEN V.cc IS NOT NULL THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0) AS DECIMAL(5,2)) AS pct_matched
FROM SC1010 SC WITH (NOLOCK)
LEFT JOIN (
  SELECT DISTINCT RTRIM(centro_custo_codigo) AS cc
  FROM dbo.vw_fin_despesas_centro_custo WITH (NOLOCK)
) V ON V.cc = RTRIM(SC.C1_CC)
WHERE SC.C1_FILIAL='01' AND SC.D_E_L_E_T_=' ' AND NULLIF(RTRIM(SC.C1_CC),'') IS NOT NULL
""",
    )
    run(
        cur,
        "cc_lookup_ctd",
        """
SELECT TOP 8 RTRIM(CTD.CTD_CUSTO) AS cc, RTRIM(CTD.CTD_DESC01) AS descr
FROM CTD010 CTD WITH (NOLOCK)
WHERE CTD.D_E_L_E_T_=' ' AND RTRIM(CTD.CTD_CUSTO) IN ('030101','0407','0501','030102')
""",
    )
    run(
        cur,
        "c7_aprov",
        """
SELECT RTRIM(C7_APROV) AS val, COUNT(*) AS cnt FROM SC7010 WITH (NOLOCK)
WHERE C7_FILIAL='01' AND D_E_L_E_T_=' ' GROUP BY RTRIM(C7_APROV) ORDER BY cnt DESC
""",
    )
    run(
        cur,
        "c1_aprov_recent",
        """
SELECT RTRIM(C1_APROV) AS val, COUNT(*) AS cnt FROM SC1010 WITH (NOLOCK)
WHERE C1_FILIAL='01' AND D_E_L_E_T_=' ' AND R_E_C_N_O_ > (SELECT MAX(R_E_C_N_O_)-5000 FROM SC1010)
GROUP BY RTRIM(C1_APROV) ORDER BY cnt DESC
""",
    )
    run(
        cur,
        "join_numsc_match",
        """
SELECT TOP 10
  RTRIM(C7.C7_NUM) AS pc, RTRIM(C7.C7_ITEM) AS pc_item,
  RTRIM(C7.C7_NUMSC) AS numsc, RTRIM(C7.C7_ITEMSC) AS itemsc,
  RTRIM(SC.C1_NUM) AS sc, RTRIM(SC.C1_ITEM) AS sc_item,
  RTRIM(SC.C1_PRODUTO) AS sc_prod, RTRIM(C7.C7_PRODUTO) AS pc_prod
FROM SC7010 C7 WITH (NOLOCK)
INNER JOIN SC1010 SC WITH (NOLOCK)
  ON RTRIM(SC.C1_NUM)=RTRIM(C7.C7_NUMSC)
 AND RTRIM(SC.C1_ITEM)=RTRIM(C7.C7_ITEMSC)
 AND SC.C1_FILIAL=C7.C7_FILIAL AND SC.D_E_L_E_T_=' '
WHERE C7.C7_FILIAL='01' AND C7.D_E_L_E_T_=' ' AND NULLIF(RTRIM(C7.C7_NUMSC),'') IS NOT NULL
ORDER BY C7.R_E_C_N_O_ DESC
""",
    )
    run(
        cur,
        "receipt_match_rate_itempc",
        """
SELECT COUNT(*) AS n,
  SUM(CASE WHEN ABS(c7_quje-sum_d1)<0.001 THEN 1 ELSE 0 END) AS exact_match,
  SUM(CASE WHEN ABS(c7_quje-sum_d1)>=0.001 THEN 1 ELSE 0 END) AS mismatch
FROM (
  SELECT TOP 300 C7.C7_QUJE AS c7_quje, COALESCE(SUM(D1.D1_QUANT),0) AS sum_d1
  FROM SC7010 C7 WITH (NOLOCK)
  LEFT JOIN SD1010 D1 WITH (NOLOCK)
    ON RTRIM(D1.D1_PEDIDO)=RTRIM(C7.C7_NUM)
   AND RTRIM(D1.D1_FORNECE)=RTRIM(C7.C7_FORNECE)
   AND RTRIM(D1.D1_LOJA)=RTRIM(C7.C7_LOJA)
   AND RTRIM(D1.D1_COD)=RTRIM(C7.C7_PRODUTO)
   AND RTRIM(D1.D1_ITEMPC)=RTRIM(C7.C7_ITEM)
   AND D1.D_E_L_E_T_=' '
  WHERE C7.C7_FILIAL='01' AND C7.D_E_L_E_T_=' ' AND C7.C7_QUJE>0
  GROUP BY C7.R_E_C_N_O_, C7.C7_QUJE, C7.C7_NUM, C7.C7_ITEM
) x
""",
    )
    run(
        cur,
        "receipt_match_rate_no_itempc",
        """
SELECT COUNT(*) AS n,
  SUM(CASE WHEN ABS(c7_quje-sum_d1)<0.001 THEN 1 ELSE 0 END) AS exact_match,
  SUM(CASE WHEN ABS(c7_quje-sum_d1)>=0.001 THEN 1 ELSE 0 END) AS mismatch
FROM (
  SELECT TOP 300 C7.C7_QUJE AS c7_quje, COALESCE(SUM(D1.D1_QUANT),0) AS sum_d1
  FROM SC7010 C7 WITH (NOLOCK)
  LEFT JOIN SD1010 D1 WITH (NOLOCK)
    ON RTRIM(D1.D1_PEDIDO)=RTRIM(C7.C7_NUM)
   AND RTRIM(D1.D1_FORNECE)=RTRIM(C7.C7_FORNECE)
   AND RTRIM(D1.D1_LOJA)=RTRIM(C7.C7_LOJA)
   AND RTRIM(D1.D1_COD)=RTRIM(C7.C7_PRODUTO)
   AND D1.D_E_L_E_T_=' '
  WHERE C7.C7_FILIAL='01' AND C7.D_E_L_E_T_=' ' AND C7.C7_QUJE>0
  GROUP BY C7.R_E_C_N_O_, C7.C7_QUJE, C7.C7_NUM, C7.C7_ITEM
) x
""",
    )
    run(
        cur,
        "scenario_E_branch02",
        """
SELECT TOP 5 RTRIM(C7_NUM) AS id, RTRIM(C7_ITEM) AS item, C7_QUANT, C7_QUJE
FROM SC7010 WITH (NOLOCK)
WHERE C7_FILIAL='02' AND D_E_L_E_T_=' ' AND C7_RESIDUO<>'S'
  AND C7_QUJE>0 AND C7_QUJE<C7_QUANT ORDER BY R_E_C_N_O_ DESC
""",
    )
    run(
        cur,
        "buyer_names",
        """
SELECT TOP 5 RTRIM(C7.C7_USER) AS code, RTRIM(U.USR_NOME) AS usr_nome, COUNT(*) AS cnt
FROM SC7010 C7 WITH (NOLOCK)
LEFT JOIN SYS_USR U ON RTRIM(U.USR_ID)=RTRIM(C7.C7_USER)
WHERE C7.C7_FILIAL='01' AND C7.D_E_L_E_T_=' '
GROUP BY RTRIM(C7.C7_USER), RTRIM(U.USR_NOME)
ORDER BY cnt DESC
""",
    )
    run(
        cur,
        "c1_cc_per_item",
        """
SELECT TOP 10 RTRIM(C1_NUM) AS sc, COUNT(DISTINCT RTRIM(C1_CC)) AS distinct_cc, COUNT(*) AS items
FROM SC1010 WITH (NOLOCK)
WHERE C1_FILIAL='01' AND D_E_L_E_T_=' ' AND NULLIF(RTRIM(C1_CC),'') IS NOT NULL
GROUP BY RTRIM(C1_NUM)
HAVING COUNT(DISTINCT RTRIM(C1_CC)) > 1
ORDER BY distinct_cc DESC
""",
    )
    run(
        cur,
        "approval_nomaprov_xgrpapr",
        """
SELECT
  SUM(CASE WHEN NULLIF(RTRIM(C1_NOMAPRO),'') IS NULL THEN 0 ELSE 1 END) AS nomaprov_filled,
  COUNT(*) AS n
FROM (SELECT TOP 500 C1_NOMAPRO FROM SC1010 WHERE C1_FILIAL='01' AND D_E_L_E_T_=' ' ORDER BY R_E_C_N_O_ DESC) x
""",
    )
    run(
        cur,
        "approval_xgrpapr_distinct",
        """
SELECT TOP 10 RTRIM(C1_XGRPAPR) AS grp, COUNT(*) AS cnt
FROM SC1010 WITH (NOLOCK)
WHERE C1_FILIAL='01' AND D_E_L_E_T_=' ' AND NULLIF(RTRIM(C1_XGRPAPR),'') IS NOT NULL
GROUP BY RTRIM(C1_XGRPAPR) ORDER BY cnt DESC
""",
    )
    run(
        cur,
        "pending_approval_sample",
        """
SELECT TOP 5 RTRIM(C1_NUM) AS sc, RTRIM(C1_APROV) AS aprov, RTRIM(C1_PEDIDO) AS pedido, C1_QUANT, C1_QUJE
FROM SC1010 WITH (NOLOCK)
WHERE C1_FILIAL='01' AND D_E_L_E_T_=' ' AND C1_RESIDUO <> 'S'
  AND RTRIM(C1_APROV) IN ('', 'B') AND C1_QUANT > C1_QUJE
ORDER BY R_E_C_N_O_ DESC
""",
    )
    run(
        cur,
        "sc_item_multi_pc",
        """
SELECT TOP 5 RTRIM(C1_NUM) AS sc, RTRIM(C1_ITEM) AS item,
  COUNT(DISTINCT RTRIM(C1_PEDIDO)) AS distinct_pcs
FROM SC1010 WITH (NOLOCK)
WHERE C1_FILIAL='01' AND D_E_L_E_T_=' ' AND NULLIF(RTRIM(C1_PEDIDO),'') IS NOT NULL
GROUP BY RTRIM(C1_NUM), RTRIM(C1_ITEM)
HAVING COUNT(DISTINCT RTRIM(C1_PEDIDO)) > 1
""",
    )

    conn.close()
    print("\nDONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
