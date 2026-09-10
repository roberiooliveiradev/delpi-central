#!/usr/bin/env python3
"""E9.S3 — candidate offline por plano 01–08 no mesmo dataset do corpus v1."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_pytest(stdout: str) -> dict[str, int]:
    passed = failed = errors = 0
    m = re.search(r"(\d+) passed", stdout)
    if m:
        passed = int(m.group(1))
    m = re.search(r"(\d+) failed", stdout)
    if m:
        failed = int(m.group(1))
    m = re.search(r"(\d+) error", stdout)
    if m:
        errors = int(m.group(1))
    return {"passed": passed, "failed": failed, "errors": errors}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    map_path = root / "tests/fixtures/intelligence_baseline/e9_s3_plan_candidate_map.json"
    corpus_path = root / "tests/fixtures/intelligence_baseline/r1_r11_corpus_v1.json"
    mapping = json.loads(map_path.read_text(encoding="utf-8"))
    dataset_hash = _sha256(corpus_path)

    if dataset_hash != mapping.get("datasetHash"):
        print("DATASET_HASH_MISMATCH", dataset_hash, mapping.get("datasetHash"))
        return 2

    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, cwd=root).strip()
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = "e9-s3-candidate-plans-offline-v1"
    run_dir = root / "docs/testing/evidence/runs" / f"{ts}_{sha[:8]}_{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)

    plan_results: list[dict] = []
    any_fail = False

    for plan in mapping["plans"]:
        refs = [str(item) for item in plan.get("harnessRefs") or []]
        missing = [ref for ref in refs if not (root / ref).is_file()]
        if missing:
            plan_results.append(
                {
                    "planId": plan["planId"],
                    "name": plan["name"],
                    "status": "FAIL",
                    "reason": "missing_harness",
                    "missing": missing,
                }
            )
            any_fail = True
            continue

        cmd = [str(root / ".venv/bin/pytest"), "-q", "--tb=line", *refs]
        proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
        counts = _parse_pytest(proc.stdout or "")
        offline_ok = proc.returncode == 0 and counts["failed"] == 0 and counts["errors"] == 0
        deferred = list(plan.get("deferredDimensions") or [])
        required = list(plan.get("requiredDimensions") or [])

        # Offline harness PASS ≠ full R1–R11 PASS when deferred dims exist.
        if not offline_ok:
            status = "FAIL"
            any_fail = True
            decision = "REGRESSION"
        elif deferred:
            status = "PASS_OFFLINE_INCONCLUSIVE_LIVE"
            decision = "NO_REGRESSION_OFFLINE"
        else:
            status = "PASS_OFFLINE"
            decision = "NO_REGRESSION_OFFLINE"

        plan_results.append(
            {
                "planId": plan["planId"],
                "name": plan["name"],
                "wave": plan.get("wave"),
                "status": status,
                "decision": decision,
                "requiredDimensions": required,
                "deferredDimensions": deferred,
                "harnessRefs": refs,
                "pytest": {
                    **counts,
                    "exitCode": proc.returncode,
                },
            }
        )
        (run_dir / f"plan-{plan['planId']}-stdout.txt").write_text(
            proc.stdout or "",
            encoding="utf-8",
        )

    aggregate_status = "FAIL" if any_fail else "PASS_OFFLINE_WITH_INCONCLUSIVE_DIMS"
    # Explicit rule: never mark global CONTENT_AUDIT-style PASS over deferred dims.
    global_pass = False

    manifest = {
        "runId": run_id,
        "wave": "H",
        "planStep": "E9.S3",
        "program": "llm-json-decoupling",
        "role": "CANDIDATE",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "gitSha": sha,
        "environment": "host-offline",
        "datasetVersion": mapping["datasetVersion"],
        "datasetHash": dataset_hash,
        "baselineRunId": mapping.get("baselineRunId"),
        "liveLlm": False,
        "globalPassForbiddenWithDeferredDims": True,
        "globalPass": global_pass,
        "aggregateStatus": aggregate_status,
        "plans": plan_results,
        "openApiSchemaHash": "PENDING_RUNTIME",
        "actionCatalogHash": "PENDING_RUNTIME",
        "notes": mapping.get("notes") or [],
    }

    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (run_dir / "results.json").write_text(
        json.dumps({"plans": plan_results}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    mirror = root / "docs/roadmap/llm-json-decoupling/evidence/e9-s3-candidate-plans-offline-v1"
    mirror.mkdir(parents=True, exist_ok=True)
    (mirror / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (mirror / "results.json").write_text(
        json.dumps({"plans": plan_results}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps({"runDir": str(run_dir), "aggregateStatus": aggregate_status}, indent=2))
    return 1 if any_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
