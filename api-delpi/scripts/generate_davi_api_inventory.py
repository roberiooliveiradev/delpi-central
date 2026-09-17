#!/usr/bin/env python3
"""Generate DAVI API DELPI operation inventory (evidence, not runtime authority)."""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.application.external_capabilities.dynamic_information.catalog_builder import (  # noqa: E402
    build_technical_actions_from_baseline,
)
from app.application.external_capabilities.dynamic_information.content_loader import (  # noqa: E402
    load_external_read_allowlist,
)
from app.application.external_capabilities.dynamic_information.eligibility import (  # noqa: E402
    is_dynamically_executable,
)


def _committed_json(rel_from_repo: str) -> dict:
    """Last committed artifact — used so re-runs keep the Wave delta vs HEAD."""
    try:
        raw = subprocess.check_output(
            ["git", "show", f"HEAD:{rel_from_repo}"],
            cwd=ROOT.parent,
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return json.loads(raw)
    except (subprocess.CalledProcessError, json.JSONDecodeError, OSError):
        return {}


def main() -> int:
    load_external_read_allowlist.cache_clear()
    baseline = json.loads(
        (ROOT / "app/content/openapi_baseline.json").read_text(encoding="utf-8")
    )
    allowlist = load_external_read_allowlist()
    actions = build_technical_actions_from_baseline(baseline, allowlist=allowlist)
    counts = Counter(a.davi_status for a in actions)
    methods = Counter(a.method for a in actions)
    eligible = [a for a in actions if is_dynamically_executable(a.davi_status)]

    out_dir = ROOT / "docs/integrations/evidence"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "davi-api-delpi-operation-inventory.json"
    previous = _committed_json(
        "api-delpi/docs/integrations/evidence/davi-api-delpi-operation-inventory.json"
    )
    if not previous and json_path.exists():
        try:
            previous = json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            previous = {}

    prev_ids = set(previous.get("ELIGIBLE_OPERATION_IDS") or [])
    cur_ids = {a.operation_id for a in eligible}
    prev_total = int(previous.get("TOTAL_OPERATIONS") or 0)
    prev_get = int(previous.get("TOTAL_GET") or 0)
    prev_eligible = int(previous.get("DAVI_ELIGIBLE_READ") or 0)

    high_value = []
    for item in allowlist.get("explicitlyNotApproved") or []:
        if isinstance(item, dict) and item.get("operationId"):
            high_value.append(
                {
                    "operationId": item.get("operationId"),
                    "primaryBlocker": item.get("primaryBlocker")
                    or item.get("davi_status")
                    or "QUARANTINED",
                    "reason": item.get("reason"),
                }
            )

    report = {
        "source": "openapi_baseline.json",
        "baseline_version": baseline.get("version"),
        "baseline_operation_count": baseline.get("operation_count"),
        "taskId": "DAVI-PRODUCT-DRAWING-CAPABILITY-001",
        "TOTAL_OPERATIONS": len(actions),
        "TOTAL_GET": methods.get("GET", 0),
        "TOTAL_WRITE_VERBS": sum(
            methods.get(m, 0) for m in ("POST", "PUT", "PATCH", "DELETE")
        ),
        "DAVI_ELIGIBLE_READ": len(eligible),
        "ELIGIBLE_BEFORE": prev_eligible,
        "ELIGIBLE_AFTER": len(eligible),
        "NEWLY_ELIGIBLE": sorted(cur_ids - prev_ids),
        "REMOVED_ELIGIBLE": sorted(prev_ids - cur_ids),
        "INVENTORY_DELTA": {
            "previous_total_operations": prev_total,
            "current_total_operations": len(actions),
            "previous_total_get": prev_get,
            "current_total_get": methods.get("GET", 0),
            "added_operations": max(0, len(actions) - prev_total) if prev_total else 0,
            "removed_operations": max(0, prev_total - len(actions)) if prev_total else 0,
            "note": "Delta vs last committed inventory artifact (HEAD)",
        },
        "COVERAGE_DECISION": allowlist.get("coverageDecision"),
        "HIGH_VALUE_BLOCKED": high_value,
        "STATUS_COUNTS": dict(sorted(counts.items())),
        "ELIGIBLE_OPERATION_IDS": sorted(a.operation_id for a in eligible),
        "MATRIX": [
            {
                "operationId": a.operation_id,
                "method": a.method,
                "path": a.path,
                "summary": a.summary,
                "entity": a.entity,
                "shape": a.shape,
                "davi_status": a.davi_status,
                "executable": a.executable,
            }
            for a in sorted(actions, key=lambda x: (x.davi_status, x.operation_id))
        ],
    }
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    md_lines = [
        "# DAVI — API DELPI operation inventory (generated)",
        "",
        "> Evidence artifact. Not runtime authority. Not semantic capability catalog.",
        "",
        f"- Task: `{report['taskId']}`",
        f"- Source: `{report['source']}` version `{report['baseline_version']}`",
        f"- TOTAL OPERATIONS: **{report['TOTAL_OPERATIONS']}**",
        f"- TOTAL GET: **{report['TOTAL_GET']}**",
        f"- WRITE VERBS (POST/PUT/PATCH/DELETE): **{report['TOTAL_WRITE_VERBS']}**",
        f"- DAVI_ELIGIBLE_READ (before→after): **{report['ELIGIBLE_BEFORE']} → {report['ELIGIBLE_AFTER']}**",
        f"- NEWLY ELIGIBLE: **{len(report['NEWLY_ELIGIBLE'])}**",
        "",
        "## Coverage decision",
        "",
        "```json",
        json.dumps(report.get("COVERAGE_DECISION") or {}, indent=2, ensure_ascii=False),
        "```",
        "",
        "## Inventory delta",
        "",
        "```json",
        json.dumps(report["INVENTORY_DELTA"], indent=2, ensure_ascii=False),
        "```",
        "",
        "## Status counts",
        "",
        "| Status | Count |",
        "|---|---:|",
    ]
    for status, count in sorted(counts.items()):
        md_lines.append(f"| `{status}` | {count} |")
    md_lines.extend(
        [
            "",
            "## Eligible operationIds",
            "",
        ]
    )
    for oid in report["ELIGIBLE_OPERATION_IDS"]:
        md_lines.append(f"- `{oid}`")
    md_lines.extend(["", "## High-value blocked (primary blocker)", ""])
    for row in high_value:
        md_lines.append(
            f"- `{row['operationId']}` → `{row['primaryBlocker']}` — {row.get('reason') or ''}"
        )
    md_lines.append("")
    (out_dir / "davi-api-delpi-operation-inventory.md").write_text(
        "\n".join(md_lines), encoding="utf-8"
    )

    coverage_path = out_dir / "davi-governed-read-coverage-product-drawing-001.json"
    coverage = {k: report[k] for k in report if k != "MATRIX"}
    coverage_path.write_text(
        json.dumps(coverage, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(json.dumps({k: report[k] for k in report if k != "MATRIX"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
