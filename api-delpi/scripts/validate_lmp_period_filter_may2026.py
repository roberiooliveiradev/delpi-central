#!/usr/bin/env python3
"""Valida filtro de período LMP maio/2026 — dashboard + diff vs first_eng legado."""
from __future__ import annotations

import json

from app.composition.engineering_composer import build_engineering_list_lmps_dashboard_use_case
from app.interface.http.routes.engineering.lmp_route_helpers import build_list_lmp_request

PERIOD_START = "2026-05-01"
PERIOD_END = "2026-05-31"

JUNE_ANCHOR_OVS = ("003562", "003578", "000120")
INTERNAL_EXTRA = ("000087", "003561", "000102", "002871", "000061")
WANKE_MULTI = ("000088", "000089", "000095")


def _fmt(d: str | None) -> str:
    if not d or len(d) != 8:
        return d or ""
    return f"{d[6:8]}/{d[4:6]}/{d[0:4]}"


def main() -> None:
    uc = build_engineering_list_lmps_dashboard_use_case()
    dto = build_list_lmp_request(
        date_start=PERIOD_START,
        date_end=PERIOD_END,
        listing_type="LMP",
        page_size=500,
    )
    items = uc.execute_items(dto, status_filter="Todos")["items"]
    summary = uc.execute_summary(dto, status_filter="Todos")

    may_anchor = [i for i in items if (i.get("start_date") or "") <= "20260531"]
    june_anchor = [i for i in items if (i.get("start_date") or "") > "20260531"]

    report = {
        "period": {"start": PERIOD_START, "end": PERIOD_END},
        "summary": summary,
        "total_items": len(items),
        "may_anchor_count": len(may_anchor),
        "june_anchor_still_listed": [
            {
                "sale_number": i["sale_number"],
                "start_date": i.get("start_date"),
                "start_fmt": _fmt(i.get("start_date")),
                "description": (i.get("sale_description") or "")[:50],
            }
            for i in june_anchor
        ],
        "wanke_ovs": [i["sale_number"] for i in items if i["sale_number"] in WANKE_MULTI],
        "extras_not_in_control": [
            i["sale_number"] for i in items if i["sale_number"] in INTERNAL_EXTRA
        ],
        "all_sale_numbers": sorted(i["sale_number"] for i in items),
        "items": [
            {
                "sale_number": i["sale_number"],
                "branch": i.get("branch"),
                "start_date": i.get("start_date"),
                "start_fmt": _fmt(i.get("start_date")),
                "status": i.get("status"),
                "lead_time_util": i.get("lead_time_util"),
                "description": (i.get("sale_description") or "")[:55],
            }
            for i in sorted(items, key=lambda x: x.get("start_date") or "")
        ],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
