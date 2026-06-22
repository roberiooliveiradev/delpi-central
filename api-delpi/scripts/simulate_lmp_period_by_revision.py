#!/usr/bin/env python3
"""Simula políticas LMP por revisão em abr/mai/Q2-2026."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

BASE = os.environ.get("API_DELPI_BASE", "http://localhost/apps/api-delpi")
TOKEN = os.environ.get("API_DELPI_INTERNAL_SERVICE_TOKEN", "")

PERIODS = [
    ("abril/2026", "20260401", "20260430"),
    ("maio/2026", "20260501", "20260531"),
    ("Q2/2026 (abr-jun)", "20260401", "20260630"),
]

EXTRAS = {"000087", "000102", "003561", "002871", "000061"}


def run_sql(sql: str) -> dict:
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
        return json.load(resp)


def dashboard_count(start: str, end: str) -> tuple[int, list[dict]]:
    ds = f"{start[:4]}-{start[4:6]}-{start[6:8]}"
    de = f"{end[:4]}-{end[4:6]}-{end[6:8]}"
    req = urllib.request.Request(
        f"{BASE}/engineering/lmps/dashboard/items?date_start={ds}&date_end={de}&listing_type=LMP",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.load(resp)["data"]["items"]
    return len(data), data


def main() -> None:
    if not TOKEN:
        raise SystemExit("Defina API_DELPI_INTERNAL_SERVICE_TOKEN")

    template = (
        Path(__file__).resolve().parent
        / "sql"
        / "lmp_period_policy_simulation_by_revision.sql"
    ).read_text(encoding="utf-8")

    for label, start, end in PERIODS:
        print("\n" + "=" * 72)
        print(f"PERÍODO: {label}  ({start} – {end})")
        print("=" * 72)

        sql = template.replace(
            "@date_start CHAR(8) = '20260501';",
            f"@date_start CHAR(8) = '{start}';",
        )
        sql = sql.replace(
            "@date_end   CHAR(8) = '20260531';",
            f"@date_end   CHAR(8) = '{end}';",
        )

        try:
            payload = run_sql(sql)
        except urllib.error.HTTPError as exc:
            print("SQL ERROR:", exc.read().decode()[:800])
            continue

        if not payload.get("success"):
            print("API ERROR:", payload)
            continue

        for rs in payload.get("data", {}).get("resultsets", []):
            rows = rs.get("data", [])
            totals = [r for r in rows if r.get("row_kind") == "TOTAL"]
            details = [r for r in rows if r.get("row_kind") == "DETAIL_HOMOLOG_REV"]
            only_cur = [r for r in rows if r.get("row_kind") == "ONLY_CURRENT_OV"]

            print("\n--- TOTAIS ---")
            for t in totals:
                print(f"  {t.get('metric_name')}: {t.get('metric_value')}")

            print(f"\n--- DETALHE homolog/revisão ({len(details)} linhas) ---")
            for row in details[:35]:
                print(json.dumps({
                    "ov": row.get("sale_number"),
                    "branch": row.get("branch"),
                    "revision": row.get("revision"),
                    "homolog": row.get("homolog_date"),
                    "eng_min": row.get("eng_minutes_closed"),
                    "tipo": row.get("tipo_proposto_strict"),
                    "also_current": row.get("also_in_politica_atual_ov"),
                }, ensure_ascii=False))
            if len(details) > 35:
                print(f"... (+{len(details) - 35})")

            if only_cur:
                print(f"\n--- Só política atual OV-level ({len(only_cur)}) ---")
                for row in only_cur[:15]:
                    print(json.dumps({
                        "ov": row.get("sale_number"),
                        "rev": row.get("revision"),
                        "homolog": row.get("homolog_date"),
                        "eng_min": row.get("eng_minutes_closed"),
                        "desc": (row.get("sale_description") or "")[:40],
                    }, ensure_ascii=False))

        try:
            dash_n, dash_items = dashboard_count(start, end)
            print(f"\nDashboard API listing_type=LMP: {dash_n}")
            for ov in sorted(EXTRAS):
                sn = ov.zfill(6)
                for h in dash_items:
                    if str(h.get("sale_number", "")).zfill(6) != sn:
                        continue
                    print(
                        f"  {sn} branch={h.get('branch')} start={h.get('start_date')} "
                        f"eng_min={h.get('engineering_total_minutes')}"
                    )
        except Exception as exc:
            print("Dashboard skip:", exc)


if __name__ == "__main__":
    main()
