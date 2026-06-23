#!/usr/bin/env python3
"""Histórico AIJ das OVs divergentes — maio/2026 RQ-060 vs dashboard."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.composition.engineering_composer import (  # noqa: E402
    build_engineering_get_lmp_history_events_use_case,
    build_engineering_get_lmp_use_case,
    build_engineering_list_lmps_dashboard_use_case,
)
from app.interface.http.routes.engineering.lmp_route_helpers import (  # noqa: E402
    build_get_lmp_history_request,
    build_get_lmp_request,
    build_list_lmp_request,
)

PERIOD_START = "2026-05-01"
PERIOD_END = "2026-05-31"
P_START = "20260501"
P_END = "20260531"

CASES: dict[str, dict[str, str]] = {
    "A_rq_ausente_dashboard": {
        "003567": "078 26 — RQ mai, ausente dashboard",
    },
    "B_extra_wanke_sem_rq": {
        "000088": "Wanke 9048 — extra vs RQ 073 (000102)",
        "000089": "Wanke 9048 — extra vs RQ 073",
        "000095": "Wanke 9048 — extra vs RQ 073",
        "000102": "RQ 073 — referência Wanke",
    },
    "C_extra_operacional_sem_rq": {
        "000087": "COLORMAQ — sem pasta RQ mai",
        "003561": "FRANKLIN — sem pasta RQ mai",
        "002871": "TRACTIAN — sem pasta RQ mai",
    },
    "D_bleed_first_eng": {
        "000120": "RQ jun 095 — âncora jun, first_eng mai",
        "003578": "RQ jun 094 — âncora jun, first_eng mai",
        "003562": "RQ mai 070 — âncora jun, first_eng mai",
    },
}


def _fmt(d: str | None) -> str:
    if not d or len(d) != 8:
        return d or ""
    return f"{d[6:8]}/{d[4:6]}/{d[0:4]}"


def _in_may(d: str | None) -> bool:
    return bool(d and len(d) == 8 and P_START <= d <= P_END)


def _summarize_event(ev: dict[str, Any]) -> dict[str, Any]:
    return {
        "rev": ev.get("revision"),
        "process": ev.get("process_code"),
        "stage": ev.get("stage_code"),
        "stage_label": ev.get("stage_label"),
        "start": ev.get("start_date"),
        "start_fmt": _fmt(ev.get("start_date")),
        "end": ev.get("end_date"),
        "end_fmt": _fmt(ev.get("end_date")),
        "is_engineering": ev.get("is_engineering"),
        "is_lmp_anchor": ev.get("is_lmp_anchor"),
        "is_sample_anchor": ev.get("is_sample_anchor"),
        "minutes": ev.get("minutes"),
    }


def _anchor_events(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for ev in items:
        stage = (ev.get("stage_code") or "").strip()
        proc = (ev.get("process_code") or "").strip()
        if stage in ("000003", "000012") and proc in ("000002", "000003"):
            out.append(_summarize_event(ev))
    return out


def _eng_events_may(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _summarize_event(ev)
        for ev in items
        if ev.get("is_engineering") and _in_may(ev.get("start_date"))
    ]


def _first_eng(items: list[dict[str, Any]]) -> dict[str, Any] | None:
    eng = [e for e in items if e.get("is_engineering") and e.get("start_date")]
    if not eng:
        return None
    eng.sort(key=lambda e: (e.get("start_date") or "", e.get("start_time") or ""))
    return _summarize_event(eng[0])


def main() -> None:
    get_uc = build_engineering_get_lmp_use_case()
    hist_uc = build_engineering_get_lmp_history_events_use_case()
    dash_uc = build_engineering_list_lmps_dashboard_use_case()

    dto_lmp = build_list_lmp_request(
        date_start=PERIOD_START, date_end=PERIOD_END, listing_type="LMP", page_size=500
    )
    dto_todos = build_list_lmp_request(
        date_start=PERIOD_START, date_end=PERIOD_END, listing_type="Todos", page_size=500
    )
    dash_lmp = {
        i["sale_number"]: i
        for i in dash_uc.execute_items(dto_lmp, status_filter="Todos")["items"]
    }
    dash_todos = {
        i["sale_number"]: i
        for i in dash_uc.execute_items(dto_todos, status_filter="Todos")["items"]
    }

    report: dict[str, Any] = {
        "period": {"start": PERIOD_START, "end": PERIOD_END},
        "categories": {},
    }

    for cat, ovs in CASES.items():
        report["categories"][cat] = []
        for ov, note in ovs.items():
            di = dash_lmp.get(ov)
            dt = dash_todos.get(ov)
            branch = (di or dt or {}).get("branch")
            detail = history = None
            errors: list[str] = []

            for br in ([branch] if branch else ["01", "02"]):
                try:
                    detail = get_uc.execute(
                        build_get_lmp_request(
                            ov, date_start=PERIOD_START, date_end=PERIOD_END, branch=br
                        )
                    )
                    history = hist_uc.execute(
                        build_get_lmp_history_request(
                            ov, date_start=PERIOD_START, date_end=PERIOD_END, branch=br
                        )
                    )
                    branch = br
                    break
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"filial {br}: {exc}")

            items = (history or {}).get("items") or []
            fe = _first_eng(items)
            anchors_may = [a for a in _anchor_events(items) if _in_may(a.get("start"))]
            eng_may = _eng_events_may(items)

            anchor_start = (di or dt or detail or {}).get("start_date")
            inclusion: list[str] = []
            if _in_may(anchor_start):
                inclusion.append("anchor_no_mes")
            if fe and _in_may(fe.get("start")):
                inclusion.append("first_eng_no_mes")

            report["categories"][cat].append(
                {
                    "ov": ov,
                    "nota": note,
                    "branch": branch,
                    "in_dashboard_lmp": ov in dash_lmp,
                    "in_dashboard_todos": ov in dash_todos,
                    "listing_kind": (detail or di or dt or {}).get("listing_kind"),
                    "engineering_status": (detail or di or dt or {}).get("engineering_status"),
                    "description": ((detail or di or dt or {}).get("sale_description") or "")[:55],
                    "anchor_start_fmt": _fmt(anchor_start),
                    "anchor_end_fmt": _fmt((detail or di or dt or {}).get("end_date")),
                    "inclusion_reason_mai": inclusion or ["nao_listada"],
                    "first_eng_global": fe,
                    "lmp_anchor_events_mai": [
                        _summarize_event(ev)
                        for ev in items
                        if ev.get("is_lmp_anchor") and _in_may(ev.get("start_date"))
                    ],
                    "anchor_markers_mai": anchors_may,
                    "engineering_events_mai": eng_may[:15],
                    "engineering_events_mai_count": len(eng_may),
                    "all_lmp_anchors": [
                        _summarize_event(ev) for ev in items if ev.get("is_lmp_anchor")
                    ][:10],
                    "all_sample_anchors": [
                        _summarize_event(ev) for ev in items if ev.get("is_sample_anchor")
                    ][:6],
                    "errors": errors,
                }
            )

    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
