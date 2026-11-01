"""R09 informational-parity probe — `Fat x MOD.xlsb` × reconstructed engine.

Run inside the api-delpi container (pyodbc + pyxlsb available). The probe
executes the real Slice-1 use case against the authorized Protheus
database (read-only) and compares deterministically against the
historical artifact, per gate 040 §11.

Usage (container):
    python /tmp/r09_parity_probe.py /tmp/fat_mod.xlsb 2026-09
"""

from __future__ import annotations

import json
import sys

import pyxlsb

sys.path.insert(0, "/app")

from app.application.dto.financeiro_billing_mod_breakdown.billing_mod_breakdown_request import (  # noqa: E402
    BillingModBreakdownRequest,
)
from app.application.security.stock_inventory_scope import (  # noqa: E402
    StockInventoryScope,
)
from app.application.use_cases.financeiro_billing_mod_breakdown.get_billing_mod_breakdown_use_case import (  # noqa: E402
    GetBillingModBreakdownUseCase,
)
from app.infrastructure.persistence.totvs.financeiro_billing_mod_breakdown.billing_mod_breakdown_repository import (  # noqa: E402
    BillingModBreakdownRepository,
)

TOL = 1e-4


class _OpenScope:
    def resolve(self, *, user_subject):
        return StockInventoryScope(resolved=True, reason="parity probe")


def _load_artifact(path: str) -> list[dict]:
    rows = []
    with pyxlsb.open_workbook(path) as wb:
        for name in wb.sheets:
            branch = "01" if name.endswith("01") else "02"
            with wb.get_sheet(name) as sheet:
                header = None
                for row in sheet.rows():
                    vals = [c.v for c in row]
                    if header is None:
                        if vals and str(vals[0]).strip() == "PA":
                            header = vals
                        continue
                    if not vals or vals[0] in (None, ""):
                        continue
                    rows.append(
                        {
                            "branch": branch,
                            "pa": str(vals[0]).strip(),
                            "level": str(vals[1]).strip(),
                            "mod": str(vals[2]).strip(),
                            "qtdfat": _f(vals[4]),
                            "qty": _f(vals[6]),
                            "hours": _f(vals[10]),
                        }
                    )
    return rows


def _f(v):
    if v in (None, ""):
        return None
    try:
        return float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return None


def _close(a, b):
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= TOL


def main() -> int:
    artifact = _load_artifact(sys.argv[1])
    period = sys.argv[2]

    uc = GetBillingModBreakdownUseCase(
        repository=BillingModBreakdownRepository(),
        scope_resolver=_OpenScope(),
    )
    request = BillingModBreakdownRequest.from_query(
        period=period, branch="all"
    )
    # Production semantics: latest OP with route as of execution.
    # The bounded variant (run_date="20261007", artifact-era) was
    # tested in Gate 042 and measured worse (3.493 vs 3.694 keys) —
    # documented hypothesis rejection, not adopted.
    data = uc.execute(
        request, user_subject="parity-probe", run_date=None
    )

    calc_lines = []
    anchors_seen = {}
    for anchor in data["anchors"]:
        anchors_seen[(anchor["branch"], anchor["product"])] = anchor[
            "billedQty"
        ]
        for line in anchor["modLines"]:
            calc_lines.append(
                {
                    "branch": anchor["branch"],
                    "pa": anchor["product"],
                    "level": line["level"],
                    "product": line["explodedProduct"],
                    "mod": line["modItem"],
                    "op": line["operation"],
                    "resource": line["resource"],
                    "qtdfat": line["propagatedQty"],
                    "qty": line["stdTime"]["value"],
                    "hours": line["hours"]["value"],
                }
            )

    # Deterministic key: branch × PA × level × MOD line position is not
    # stable across engines; compare by multiset of
    # (branch, pa, level, mod) for coverage and by joined metrics.
    from collections import Counter

    art_key = Counter(
        (r["branch"], r["pa"], r["level"], r["mod"]) for r in artifact
    )
    # Artifact's "PA" column is the exploded product, not the billed
    # anchor (proven: 70260033 appears only at level 04 and was never
    # billed; its billed parents carry it as an SG1 component).
    cal_key = Counter(
        (c["branch"], c["product"], c["level"], c["mod"])
        for c in calc_lines
    )
    matched = sum((art_key & cal_key).values())
    missing = art_key - cal_key
    extra = cal_key - art_key

    # Field-level comparison on matched keys (first occurrence).
    art_by_key = {}
    for r in artifact:
        art_by_key.setdefault(
            (r["branch"], r["pa"], r["level"], r["mod"]), []
        ).append(r)
    qty_ok = qty_bad = hours_ok = hours_bad = qtdfat_ok = qtdfat_bad = 0
    for c in calc_lines:
        key = (c["branch"], c["product"], c["level"], c["mod"])
        bucket = art_by_key.get(key)
        if not bucket:
            continue
        a = bucket.pop(0)
        if _close(a["qtdfat"], c["qtdfat"]):
            qtdfat_ok += 1
        else:
            qtdfat_bad += 1
        if _close(a["qty"], c["qty"]):
            qty_ok += 1
        else:
            qty_bad += 1
        if _close(a["hours"], c["hours"]):
            hours_ok += 1
        else:
            hours_bad += 1

    report = {
        "period": period,
        "artifact_lines": len(artifact),
        "calculated_lines": len(calc_lines),
        "anchors_calculated": len(anchors_seen),
        "keys_matched": matched,
        "keys_missing": sum(missing.values()),
        "keys_extra": sum(extra.values()),
        "qtdfat_ok": qtdfat_ok,
        "qtdfat_bad": qtdfat_bad,
        "qty_ok": qty_ok,
        "qty_bad": qty_bad,
        "hours_ok": hours_ok,
        "hours_bad": hours_bad,
        "missing_sample": [
            {"key": list(k), "count": v}
            for k, v in missing.most_common(15)
        ],
        "extra_sample": [
            {"key": list(k), "count": v}
            for k, v in extra.most_common(15)
        ],
    }
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
