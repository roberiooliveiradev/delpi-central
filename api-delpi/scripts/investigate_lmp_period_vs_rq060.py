#!/usr/bin/env python3
"""Cruza OVs do controle interno (RQ-060) com dashboard LMP da api-delpi no mês."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.composition.engineering_composer import (
    build_engineering_get_lmp_history_events_use_case,
    build_engineering_get_lmp_use_case,
    build_engineering_list_lmps_dashboard_use_case,
)
from app.interface.http.routes.engineering.lmp_route_helpers import (
    build_get_lmp_history_request,
    build_get_lmp_request,
    build_list_lmp_request,
)

_DATA_ALL = Path(__file__).resolve().parent / "data" / "lmp_2026_internal_control_ovs_all.json"


def _fmt_date(raw: str | None) -> str:
    if not raw or len(raw) != 8:
        return raw or ""
    return f"{raw[6:8]}/{raw[4:6]}/{raw[0:4]}"


def _in_period(date_raw: str | None, period_start: str, period_end: str) -> bool:
    if not date_raw or len(date_raw) != 8:
        return False
    start = period_start.replace("-", "")
    end = period_end.replace("-", "")
    return start <= date_raw <= end


def _first_eng_event(history: dict[str, Any]) -> dict[str, Any] | None:
    items = history.get("items") or []
    eng = [ev for ev in items if ev.get("is_engineering") and ev.get("start_date")]
    if not eng:
        return None
    eng.sort(key=lambda e: (e.get("start_date") or "", e.get("start_time") or ""))
    ev = eng[0]
    return {
        "start": ev.get("start_date"),
        "start_fmt": _fmt_date(ev.get("start_date")),
        "stage_label": ev.get("stage_label"),
        "revision": ev.get("revision"),
    }


def _load_rq060_rows(month: str) -> list[dict[str, Any]]:
    rows = json.loads(_DATA_ALL.read_text(encoding="utf-8"))
    return [r for r in rows if r.get("mes") == month and not r.get("error")]


def _investigate_ov(
    sale_number: str,
    *,
    period_start: str,
    period_end: str,
    get_uc,
    hist_uc,
    dashboard_item: dict[str, Any] | None,
) -> dict[str, Any]:
    branch = (dashboard_item or {}).get("branch")
    detail = None
    history = None
    errors: list[str] = []

    for br in ([branch] if branch else ["01", "02"]):
        try:
            req = build_get_lmp_request(
                sale_number,
                date_start=period_start,
                date_end=period_end,
                branch=br,
            )
            detail = get_uc.execute(req)
            hist_req = build_get_lmp_history_request(
                sale_number,
                date_start=period_start,
                date_end=period_end,
                branch=br,
            )
            history = hist_uc.execute(hist_req)
            branch = br
            break
        except Exception as exc:  # noqa: BLE001
            errors.append(f"filial {br}: {exc}")

    first_eng = _first_eng_event(history) if history else None
    anchor_start = (dashboard_item or {}).get("start_date") or (detail or {}).get("start_date")
    anchor_end = (dashboard_item or {}).get("end_date") or (detail or {}).get("end_date")

    inclusion_reason: list[str] = []
    if _in_period(anchor_start, period_start, period_end):
        inclusion_reason.append("anchor_no_mes")
    if first_eng and _in_period(first_eng.get("start"), period_start, period_end):
        inclusion_reason.append("first_eng_no_mes")
    if not inclusion_reason:
        inclusion_reason.append("fora_do_mes_ou_sem_dados")

    return {
        "sale_number": sale_number,
        "branch": branch,
        "description": (detail or dashboard_item or {}).get("sale_description", ""),
        "listing_kind": (detail or dashboard_item or {}).get("listing_kind"),
        "anchor_start": anchor_start,
        "anchor_start_fmt": _fmt_date(anchor_start),
        "anchor_end": anchor_end,
        "anchor_end_fmt": _fmt_date(anchor_end),
        "first_eng": first_eng,
        "inclusion_reason": inclusion_reason,
        "in_dashboard": dashboard_item is not None,
        "engineering_status": (detail or dashboard_item or {}).get("engineering_status"),
        "errors": errors,
    }


def _normalize_lmp_code(code: str) -> str:
    m = re.match(r"(\d+)\s*26", code.strip())
    if not m:
        return code.strip()
    return f"{int(m.group(1)):03d} 26"


def main() -> None:
    parser = argparse.ArgumentParser(description="Cruza RQ-060 vs dashboard LMP")
    parser.add_argument("--month", default="2026-06", help="Mês YYYY-MM (default: 2026-06)")
    parser.add_argument(
        "--dashboard-only",
        action="store_true",
        help="Só lista dashboard + diff (sem histórico por OV)",
    )
    args = parser.parse_args()

    year, mon = args.month.split("-")
    last_day = "30" if mon in ("04", "06", "09", "11") else "31"
    if mon == "02":
        last_day = "28"
    period_start = f"{year}-{mon}-01"
    period_end = f"{year}-{mon}-{last_day}"

    rq_rows = _load_rq060_rows(args.month)
    rq_by_ov: dict[str, list[str]] = {}
    for row in rq_rows:
        ov = (row.get("ov") or "").strip()
        code = _normalize_lmp_code(row.get("lmp_ano") or "")
        rq_by_ov.setdefault(ov, []).append(code)

    dash_uc = build_engineering_list_lmps_dashboard_use_case()
    get_uc = build_engineering_get_lmp_use_case()
    hist_uc = build_engineering_get_lmp_history_events_use_case()

    dto = build_list_lmp_request(
        date_start=period_start,
        date_end=period_end,
        listing_type="LMP",
        page_size=500,
    )
    dashboard_items = {
        it["sale_number"]: it
        for it in dash_uc.execute_items(dto, status_filter="Todos")["items"]
    }
    summary = dash_uc.execute_summary(dto, status_filter="Todos")

    rq_ovs = sorted(rq_by_ov.keys())
    dash_ovs = sorted(dashboard_items.keys())

    in_both = sorted(set(rq_ovs) & set(dash_ovs))
    rq_only = sorted(set(rq_ovs) - set(dash_ovs))
    dash_only = sorted(set(dash_ovs) - set(rq_ovs))

    folder_details = []
    for row in rq_rows:
        ov = (row.get("ov") or "").strip()
        dash_item = dashboard_items.get(ov)
        if args.dashboard_only:
            folder_details.append(
                {
                    "lmp_ano": row.get("lmp_ano"),
                    "ov_rq060": ov,
                    "ov_duplicada_em": rq_by_ov.get(ov, []),
                    "status": "ALINHADO" if dash_item else "RQ060_SEM_DASHBOARD",
                    "anchor_start_fmt": _fmt_date(dash_item.get("start_date")) if dash_item else None,
                    "description": (dash_item or {}).get("sale_description", ""),
                }
            )
            continue
        inv = _investigate_ov(
            ov,
            period_start=period_start,
            period_end=period_end,
            get_uc=get_uc,
            hist_uc=hist_uc,
            dashboard_item=dashboard_items.get(ov),
        )
        folder_details.append(
            {
                "lmp_ano": row.get("lmp_ano"),
                "ov_rq060": ov,
                "ov_duplicada_em": rq_by_ov.get(ov, []),
                "status": (
                    "ALINHADO"
                    if ov in dashboard_items
                    else "RQ060_SEM_DASHBOARD"
                ),
                **{k: inv[k] for k in ("anchor_start_fmt", "first_eng", "inclusion_reason", "description", "errors")},
            }
        )

    extras_detail = []
    for ov in dash_only:
        dash_item = dashboard_items[ov]
        if args.dashboard_only:
            extras_detail.append(
                {
                    "ov": ov,
                    "status": "DASHBOARD_SEM_RQ060",
                    "pastas_rq060": rq_by_ov.get(ov, []),
                    "anchor_start_fmt": _fmt_date(dash_item.get("start_date")),
                    "description": dash_item.get("sale_description", ""),
                }
            )
            continue
        inv = _investigate_ov(
            ov,
            period_start=period_start,
            period_end=period_end,
            get_uc=get_uc,
            hist_uc=hist_uc,
            dashboard_item=dashboard_items[ov],
        )
        extras_detail.append(
            {
                "ov": ov,
                "status": "DASHBOARD_SEM_RQ060",
                "pastas_rq060": rq_by_ov.get(ov, []),
                **{k: inv[k] for k in ("anchor_start_fmt", "first_eng", "inclusion_reason", "description")},
            }
        )

    rq_only_detail = []
    for ov in rq_only:
        if args.dashboard_only:
            rq_only_detail.append({"ov": ov, "pastas_rq060": rq_by_ov.get(ov, []), "status": "RQ060_SEM_DASHBOARD"})
            continue
        inv = _investigate_ov(
            ov,
            period_start=period_start,
            period_end=period_end,
            get_uc=get_uc,
            hist_uc=hist_uc,
            dashboard_item=None,
        )
        rq_only_detail.append(
            {
                "ov": ov,
                "pastas_rq060": rq_by_ov.get(ov, []),
                **{k: inv[k] for k in ("anchor_start_fmt", "first_eng", "inclusion_reason", "description", "errors")},
            }
        )

    dup_ovs = {ov: codes for ov, codes in rq_by_ov.items() if len(codes) > 1}

    report: dict[str, Any] = {
        "period": {"start": period_start, "end": period_end, "month": args.month},
        "summary_api": summary,
        "totals": {
            "pastas_rq060": len(rq_rows),
            "ovs_unicas_rq060": len(rq_ovs),
            "dashboard_lmp": len(dash_ovs),
            "intersecao": len(in_both),
            "somente_rq060": len(rq_only),
            "somente_dashboard": len(dash_only),
            "ovs_duplicadas_entre_pastas": len(dup_ovs),
        },
        "ovs_duplicadas_rq060": dup_ovs,
        "intersecao": in_both,
        "somente_rq060": rq_only,
        "somente_dashboard": dash_only,
        "pastas_rq060": folder_details,
        "detalhe_somente_rq060": rq_only_detail,
        "detalhe_somente_dashboard": extras_detail,
    }

    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
