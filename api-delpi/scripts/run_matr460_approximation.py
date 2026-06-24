#!/usr/bin/env python3
"""Executa modelos de aproximacao MATR460 via POST /data/sql."""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

BASE = os.environ.get("API_DELPI_BASE", "http://localhost/apps/api-delpi")
TOKEN = os.environ.get("API_DELPI_INTERNAL_SERVICE_TOKEN", "")
SQL_PATH = Path(__file__).resolve().parent / "sql" / "matr460_approximation_models.sql"

REF = {
    "01": {"ee": 3_598_312.40, "ep": 263_790.57, "tg": 3_862_102.97},
    "02": {"ee": 9_737_043.62, "ep": 311_465.89, "tg": 10_048_509.51},
}


def _pct(value: float | None, ref: float) -> str:
    if value is None or ref == 0:
        return "—"
    return f"{100.0 * value / ref:.1f}%"


def _num(value) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def main() -> int:
    if not TOKEN:
        print("Defina API_DELPI_INTERNAL_SERVICE_TOKEN", file=sys.stderr)
        return 1
    sql = SQL_PATH.read_text(encoding="utf-8")
    req = urllib.request.Request(
        f"{BASE}/data/sql",
        data=json.dumps({"sql": sql}).encode(),
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        payload = json.load(resp)

    if not payload.get("success"):
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 1

    print(f"{'Modelo':<24} {'Fil':<3} {'EM ESTOQUE':>14} {'%EE':>6} {'EM PROC':>14} {'%EP':>6} {'TOTAL':>14} {'%TG':>6}")
    print("-" * 95)
    for rs in payload.get("data", {}).get("resultsets", []):
        for row in rs.get("data", []):
            branch = str(row.get("branch") or "")
            ref = REF.get(branch, {})
            ee = _num(row.get("em_estoque"))
            ep = _num(row.get("em_processo"))
            tg = _num(row.get("total_geral"))
            print(
                f"{row.get('model',''):<24} {branch:<3} "
                f"{(ee if ee is not None else 0):>14,.2f} {_pct(ee, ref.get('ee',0)):>6} "
                f"{(ep if ep is not None else 0):>14,.2f} {_pct(ep, ref.get('ep',0)):>6} "
                f"{(tg if tg is not None else 0):>14,.2f} {_pct(tg, ref.get('tg',0)):>6}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
