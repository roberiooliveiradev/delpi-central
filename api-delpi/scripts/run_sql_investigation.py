#!/usr/bin/env python3
"""Executa SQL de investigação LMP via POST /data/sql (sem alterar repositório)."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = os.environ.get("API_DELPI_BASE", "http://localhost/apps/api-delpi")
TOKEN = os.environ.get("API_DELPI_INTERNAL_SERVICE_TOKEN", "")


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
    scripts_dir = Path(__file__).resolve().parent / "sql"
    names = sys.argv[1:] or [
        "lmp_may2026_period_filter_totals.sql",
        "lmp_may2026_period_filter_compare.sql",
    ]
    for name in names:
        path = scripts_dir / name
        sql = path.read_text(encoding="utf-8")
        print(f"\n{'=' * 60}\nFILE: {name}\n{'=' * 60}")
        try:
            payload = run_sql(sql)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode()
            print("HTTP ERROR:", exc.code, body[:500])
            continue
        if not payload.get("success"):
            print("API ERROR:", payload)
            continue
        for rs in payload.get("data", {}).get("resultsets", []):
            print(f"--- resultset {rs.get('index')} rows={rs.get('total')} ---")
            for row in rs.get("data", [])[:80]:
                print(json.dumps(row, ensure_ascii=False))
            if (rs.get("total") or 0) > 80:
                print(f"... (+{(rs.get('total') or 0) - 80} linhas)")


if __name__ == "__main__":
    main()
