#!/usr/bin/env python3
"""Fase 0 — probes SQL para módulo refugos via POST /data/sql."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

BASE = os.environ.get("API_DELPI_BASE", "http://localhost:8000")
TOKEN = os.environ.get("API_DELPI_INTERNAL_SERVICE_TOKEN", "")

PROBES = {
    "sample_joins": """
SELECT TOP 5
    BC.BC_FILIAL,
    BC.BC_DATA,
    RTRIM(BC.BC_OP) AS OP,
    RTRIM(BC.BC_PRODUTO) AS MP,
    RTRIM(BC.BC_MOTIVO) AS MOTIVO,
    BC.BC_QUANT,
    RTRIM(BC.BC_RECURSO) AS RECURSO,
    RTRIM(BC.BC_OPERADO) AS OPERADO,
    RTRIM(BC.BC_TIPO) AS TIPO,
    RTRIM(SB1.B1_DESC) AS DESC_MP,
    SB1.B1_UM,
    SB1.B1_CUSTD,
    SB2.B2_CM1,
    RTRIM(OP.C2_PRODUTO) AS PA,
    BC.BC_QUANT * COALESCE(NULLIF(SB2.B2_CM1, 0), NULLIF(SB1.B1_CUSTD, 0), 0) AS VALOR
FROM SBC010 BC WITH (NOLOCK)
INNER JOIN SB1010 SB1 WITH (NOLOCK)
    ON SB1.B1_COD = BC.BC_PRODUTO AND SB1.D_E_L_E_T_ = ''
LEFT JOIN SB2010 SB2 WITH (NOLOCK)
    ON SB2.B2_FILIAL = BC.BC_FILIAL
   AND SB2.B2_COD = BC.BC_PRODUTO
   AND SB2.D_E_L_E_T_ = ''
LEFT JOIN SC2010 OP WITH (NOLOCK)
    ON OP.C2_FILIAL = BC.BC_FILIAL
   AND OP.C2_OP = BC.BC_OP
   AND OP.D_E_L_E_T_ = ''
WHERE BC.D_E_L_E_T_ = ''
  AND BC.BC_TIPO = 'R'
  AND BC.BC_DATA >= '20260401'
  AND BC.BC_DATA < '20260428'
ORDER BY BC.BC_DATA DESC
""",
    "resumo_valor": """
SELECT
    SUM(BC.BC_QUANT * COALESCE(NULLIF(SB2.B2_CM1, 0), NULLIF(SB1.B1_CUSTD, 0), 0)) AS TOTAL_VALOR,
    SUM(BC.BC_QUANT) AS TOTAL_QTD,
    COUNT(*) AS OCORRENCIAS,
    SUM(CASE WHEN COALESCE(NULLIF(SB2.B2_CM1, 0), NULLIF(SB1.B1_CUSTD, 0), 0) = 0 THEN 1 ELSE 0 END) AS SEM_CUSTO
FROM SBC010 BC WITH (NOLOCK)
INNER JOIN SB1010 SB1 WITH (NOLOCK)
    ON SB1.B1_COD = BC.BC_PRODUTO AND SB1.D_E_L_E_T_ = ''
LEFT JOIN SB2010 SB2 WITH (NOLOCK)
    ON SB2.B2_FILIAL = BC.BC_FILIAL
   AND SB2.B2_COD = BC.BC_PRODUTO
   AND SB2.D_E_L_E_T_ = ''
WHERE BC.D_E_L_E_T_ = ''
  AND BC.BC_TIPO = 'R'
  AND BC.BC_FILIAL = '01'
  AND BC.BC_DATA >= '20260401'
  AND BC.BC_DATA < '20260428'
""",
    "top_motivo": """
SELECT TOP 10
    RTRIM(BC.BC_MOTIVO) AS MOTIVO,
    SUM(BC.BC_QUANT * COALESCE(NULLIF(SB2.B2_CM1, 0), NULLIF(SB1.B1_CUSTD, 0), 0)) AS VALOR,
    SUM(BC.BC_QUANT) AS QTD,
    COUNT(*) AS OCORRENCIAS
FROM SBC010 BC WITH (NOLOCK)
INNER JOIN SB1010 SB1 WITH (NOLOCK)
    ON SB1.B1_COD = BC.BC_PRODUTO AND SB1.D_E_L_E_T_ = ''
LEFT JOIN SB2010 SB2 WITH (NOLOCK)
    ON SB2.B2_FILIAL = BC.BC_FILIAL
   AND SB2.B2_COD = BC.BC_PRODUTO
   AND SB2.D_E_L_E_T_ = ''
WHERE BC.D_E_L_E_T_ = ''
  AND BC.BC_TIPO = 'R'
  AND BC.BC_FILIAL = '01'
  AND BC.BC_DATA >= '20260401'
  AND BC.BC_DATA < '20260428'
GROUP BY RTRIM(BC.BC_MOTIVO)
ORDER BY VALOR DESC
""",
    "sbc_columns_sample": """
SELECT TOP 1 *
FROM SBC010 BC WITH (NOLOCK)
WHERE BC.D_E_L_E_T_ = '' AND BC.BC_TIPO = 'R'
""",
    "cyo_exists": """
SELECT TOP 5 TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_NAME LIKE 'CYO%'
""",
}


def run_sql(sql: str) -> dict:
    if not TOKEN:
        raise SystemExit("Defina API_DELPI_INTERNAL_SERVICE_TOKEN")
    req = urllib.request.Request(
        f"{BASE}/data/sql",
        data=json.dumps({"sql": sql}).encode(),
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.load(resp)


def main() -> None:
    names = sys.argv[1:] if (sys := __import__("sys")).argv[1:] else list(PROBES)
    for name in names:
        sql = PROBES[name]
        print(f"\n{'=' * 60}\nPROBE: {name}\n{'=' * 60}")
        try:
            payload = run_sql(sql)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode()
            print("HTTP ERROR:", exc.code, body[:800])
            continue
        except Exception as exc:
            print("ERR:", exc)
            continue
        if not payload.get("success"):
            print("API ERROR:", json.dumps(payload, ensure_ascii=False)[:800])
            continue
        for rs in payload.get("data", {}).get("resultsets", []):
            print(f"--- rows={rs.get('total')} ---")
            cols = rs.get("columns") or []
            if cols and name == "sbc_columns_sample":
                print("COLUMNS:", [c.get("name") if isinstance(c, dict) else c for c in cols])
            for row in (rs.get("data") or [])[:30]:
                print(json.dumps(row, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
