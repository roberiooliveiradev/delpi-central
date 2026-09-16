#!/usr/bin/env python3
"""Generate DAVI API DELPI operation inventory (evidence, not runtime authority)."""

from __future__ import annotations

import json
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


def main() -> int:
    baseline = json.loads(
        (ROOT / "app/content/openapi_baseline.json").read_text(encoding="utf-8")
    )
    allowlist = load_external_read_allowlist()
    actions = build_technical_actions_from_baseline(baseline, allowlist=allowlist)
    counts = Counter(a.davi_status for a in actions)
    methods = Counter(a.method for a in actions)
    eligible = [a for a in actions if is_dynamically_executable(a.davi_status)]
    report = {
        "source": "openapi_baseline.json",
        "baseline_version": baseline.get("version"),
        "baseline_operation_count": baseline.get("operation_count"),
        "TOTAL_OPERATIONS": len(actions),
        "TOTAL_GET": methods.get("GET", 0),
        "TOTAL_WRITE_VERBS": sum(
            methods.get(m, 0) for m in ("POST", "PUT", "PATCH", "DELETE")
        ),
        "DAVI_ELIGIBLE_READ": len(eligible),
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
    out_dir = ROOT / "docs/integrations/evidence"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "davi-api-delpi-operation-inventory.json"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    md_lines = [
        "# DAVI — API DELPI operation inventory (generated)",
        "",
        "> Evidence artifact. Not runtime authority. Not semantic capability catalog.",
        "",
        f"- Source: `{report['source']}` version `{report['baseline_version']}`",
        f"- TOTAL OPERATIONS: **{report['TOTAL_OPERATIONS']}**",
        f"- TOTAL GET: **{report['TOTAL_GET']}**",
        f"- WRITE VERBS (POST/PUT/PATCH/DELETE): **{report['TOTAL_WRITE_VERBS']}**",
        f"- DAVI_ELIGIBLE_READ: **{report['DAVI_ELIGIBLE_READ']}**",
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
    md_lines.append("")
    (out_dir / "davi-api-delpi-operation-inventory.md").write_text(
        "\n".join(md_lines), encoding="utf-8"
    )
    print(json.dumps({k: report[k] for k in report if k != "MATRIX"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
