#!/usr/bin/env python3
"""
Gate: simula políticas LMP em SQL e cruza com RQ-060 + dashboard atual.

Use ANTES de alterar LMPQueryRepository / period_inclusion_policy.

  docker exec -w /app delpi-api-delpi python scripts/validate_lmp_period_policies_vs_rq060.py --month 2026-06
  docker exec -w /app delpi-api-delpi python scripts/validate_lmp_period_policies_vs_rq060.py --month 2026-05 --no-dashboard

Saída: totais por política, interseção com OVs do RQ, OVs só RQ / só política.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.composition.engineering_composer import (
    build_engineering_list_lmps_dashboard_use_case,
)
from app.infrastructure.persistence.totvs.lmp_repositories.lmp_query_repository import (
    LMPQueryRepository,
)
from app.interface.http.routes.engineering.lmp_route_helpers import build_list_lmp_request

_SQL_GATE = Path(__file__).resolve().parent / "sql" / "lmp_period_policy_gate_compare.sql"
_DATA_RQ = Path(__file__).resolve().parent / "data" / "lmp_2026_internal_control_ovs_all.json"

POLICY_OV_KEY = {
    "anchor_in_period_ov": "ovs_distintas",
    "homolog_rev_in_period": "ovs_distintas",
    "eng_rev_work_month": "ovs_distintas",
    "eng_rev_first_eng_only": "ovs_distintas",
}


def _month_bounds(month: str) -> tuple[str, str, str, str]:
    """YYYY-MM → (iso_start, iso_end, yyyymmdd_start, yyyymmdd_end)."""
    year, mon = month.split("-", 1)
    last_day = {
        "01": "31", "02": "28", "03": "31", "04": "30", "05": "31", "06": "30",
        "07": "31", "08": "31", "09": "30", "10": "31", "11": "30", "12": "31",
    }[mon]
    iso_start = f"{year}-{mon}-01"
    iso_end = f"{year}-{mon}-{last_day}"
    return iso_start, iso_end, iso_start.replace("-", ""), iso_end.replace("-", "")


def _load_rq_ovs(month: str) -> set[str]:
    rows = json.loads(_DATA_RQ.read_text(encoding="utf-8"))
    ovs: set[str] = set()
    for row in rows:
        if row.get("mes") != month or row.get("error"):
            continue
        ov = str(row.get("ov") or row.get("ov_rq060") or "").strip()
        if ov:
            ovs.add(ov.zfill(6))
    return ovs


def _run_gate_sql(date_start: str, date_end: str) -> list[dict[str, Any]]:
    template = _SQL_GATE.read_text(encoding="utf-8")
    sql = template.replace(
        "DECLARE @date_start CHAR(8) = '20260601';",
        f"DECLARE @date_start CHAR(8) = '{date_start}';",
    )
    sql = sql.replace(
        "DECLARE @date_end   CHAR(8) = '20260630';",
        f"DECLARE @date_end   CHAR(8) = '{date_end}';",
    )
    with LMPQueryRepository() as repo:
        return repo.execute_query(sql, ())


def _parse_gate_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_policy: dict[str, dict[str, Any]] = {}
    for row in rows:
        policy = row.get("policy_name") or ""
        bucket = by_policy.setdefault(
            policy,
            {"totals": {}, "detail_ovs": set(), "details": []},
        )
        if row.get("row_kind") == "TOTAL":
            metric = row.get("metric_name")
            if metric:
                bucket["totals"][metric] = row.get("metric_value")
        elif row.get("row_kind") == "DETAIL" and row.get("sale_number"):
            ov = str(row["sale_number"]).strip().zfill(6)
            bucket["detail_ovs"].add(ov)
            bucket["details"].append(row)
    return by_policy


def _dashboard_ovs(iso_start: str, iso_end: str) -> set[str]:
    uc = build_engineering_list_lmps_dashboard_use_case()
    dto = build_list_lmp_request(
        date_start=iso_start,
        date_end=iso_end,
        listing_type="LMP",
        page_size=500,
    )
    items = uc.execute_items(dto, status_filter="Todos")["items"]
    return {str(i["sale_number"]).zfill(6) for i in items}


def _compare_sets(label: str, policy_ovs: set[str], rq_ovs: set[str]) -> dict[str, Any]:
    return {
        "policy": label,
        "policy_count": len(policy_ovs),
        "rq_count": len(rq_ovs),
        "intersection": len(policy_ovs & rq_ovs),
        "only_rq": sorted(rq_ovs - policy_ovs),
        "only_policy": sorted(policy_ovs - rq_ovs),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Gate políticas LMP vs RQ-060")
    parser.add_argument("--month", required=True, help="YYYY-MM (ex.: 2026-06)")
    parser.add_argument(
        "--no-dashboard",
        action="store_true",
        help="Pula consulta ao dashboard (só SQL gate)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Saída JSON completa",
    )
    args = parser.parse_args()

    iso_start, iso_end, yyyymm_start, yyyymm_end = _month_bounds(args.month)
    rq_ovs = _load_rq_ovs(args.month)
    gate_rows = _run_gate_sql(yyyymm_start, yyyymm_end)
    policies = _parse_gate_rows(gate_rows)

    dashboard_ovs: set[str] = set()
    if not args.no_dashboard:
        dashboard_ovs = _dashboard_ovs(iso_start, iso_end)

    report: dict[str, Any] = {
        "month": args.month,
        "period": {"start": iso_start, "end": iso_end},
        "rq_ovs_unique": len(rq_ovs),
        "rq_ovs": sorted(rq_ovs),
        "policies": {},
        "dashboard": {
            "count": len(dashboard_ovs),
            "vs_rq": _compare_sets("dashboard_atual", dashboard_ovs, rq_ovs),
        }
        if dashboard_ovs or not args.no_dashboard
        else None,
    }

    for policy_name, data in sorted(policies.items()):
        policy_ovs = data["detail_ovs"]
        report["policies"][policy_name] = {
            "totals": data["totals"],
            "vs_rq": _compare_sets(policy_name, policy_ovs, rq_ovs),
        }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    print(f"\n{'=' * 72}")
    print(f"GATE LMP — {args.month}  ({iso_start} … {iso_end})")
    print(f"RQ-060 OVs únicas: {len(rq_ovs)}")
    print("=" * 72)

    if report.get("dashboard"):
        d = report["dashboard"]["vs_rq"]
        print(
            f"\n[dashboard_atual] linhas={report['dashboard']['count']} "
            f"inter_rq={d['intersection']} só_rq={len(d['only_rq'])} só_dash={len(d['only_policy'])}"
        )

    for policy_name, block in report["policies"].items():
        totals = block["totals"]
        cmp_ = block["vs_rq"]
        print(f"\n[{policy_name}] totals={totals}")
        print(
            f"  vs RQ: inter={cmp_['intersection']} "
            f"só_rq={len(cmp_['only_rq'])} só_pol={len(cmp_['only_policy'])}"
        )
        if cmp_["only_rq"]:
            print(f"  só RQ: {', '.join(cmp_['only_rq'][:12])}"
                  f"{'…' if len(cmp_['only_rq']) > 12 else ''}")
        if cmp_["only_policy"]:
            print(f"  só política: {', '.join(cmp_['only_policy'][:12])}"
                  f"{'…' if len(cmp_['only_policy']) > 12 else ''}")

    print(
        "\n→ Só altere LMPQueryRepository após escolher política com interseção aceitável.\n"
        "  SQL: scripts/sql/lmp_period_policy_gate_compare.sql\n"
    )


if __name__ == "__main__":
    main()
