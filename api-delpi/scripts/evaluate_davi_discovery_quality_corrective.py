"""DAVI discovery-quality corrective evidence runner.

Runs the frozen benchmark (``davi_discovery_quality_v1``) against the current
retrieval source and diffs it against the accepted baseline evidence artifact
(``davi-mcp-discovery-quality-001.json``). Produces deterministic before/after
metrics, family metrics, root-cause deltas and the regression matrix required
by DAVI-MCP-DISCOVERY-QUALITY-CORRECTIVE-001.

No network, no provider calls, no business execution, no candidate tokens in
output. Usage:

    python scripts/evaluate_davi_discovery_quality_corrective.py            # summary
    python scripts/evaluate_davi_discovery_quality_corrective.py --write    # evidence JSON

Provenance flags (use when git is unavailable, e.g. inside the app container):

    --runtime-source-sha <sha>   HEAD of the source tree being evaluated
    --fixture-sha256-baseline <hex>  sha256 of the fixture at the baseline commit
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

_API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_API_ROOT))
sys.path.insert(0, str(_API_ROOT / "scripts"))

from evaluate_davi_discovery_quality import (  # noqa: E402
    _FIXTURE,
    _POSITIVE_TYPES,
    _load_fixture,
    evaluate,
)

_BASELINE_EVIDENCE = (
    _API_ROOT
    / "docs/integrations/evidence/davi-mcp-discovery-quality-001.json"
)
_EVIDENCE = (
    _API_ROOT
    / "docs/integrations/evidence/davi-mcp-discovery-quality-corrective-001.json"
)
_CASE_ID = "DQ-STOCK-001"


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_sha() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=_API_ROOT.parent,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except Exception:
        return "UNKNOWN"


def _fixture_sha256_at(commit: str) -> str:
    """sha256 of the frozen fixture at a git commit (proves immutability)."""
    rel = _FIXTURE.relative_to(_API_ROOT.parent.parent / "api-delpi")
    out = subprocess.run(
        ["git", "show", f"{commit}:api-delpi/{rel.as_posix()}"],
        cwd=_API_ROOT.parent,
        capture_output=True,
        check=True,
    ).stdout
    return hashlib.sha256(out).hexdigest()


def _baseline_maps(evidence: dict) -> tuple[dict, dict]:
    """Baseline per-case outcomes reconstructed from the accepted artifact."""
    failures = {f["id"]: f for f in evidence.get("known_failures", [])}
    metrics = evidence.get("metrics", {})
    return failures, metrics


def _regression_matrix(before_failures: dict, after_results: dict, after: dict) -> dict:
    """Compare baseline outcome classes against the corrected results.

    Baseline top1 wins are the positive cases absent from ``known_failures``;
    baseline rank 2-5 wins carry ``target_rank`` in that artifact.
    """
    lost_top1, lost_top3, lost_top5 = [], [], []
    new_zero_candidate = []
    for cid, r in after_results.items():
        if r["case_type"] not in _POSITIVE_TYPES:
            continue
        before = before_failures.get(cid)
        before_rank = 1 if before is None else before.get("target_rank")
        after_rank = r["target_rank"]
        if before_rank == 1 and (after_rank is None or after_rank != 1):
            lost_top1.append(cid)
        if before_rank is not None and before_rank <= 3 and (
            after_rank is None or after_rank > 3
        ):
            lost_top3.append(cid)
        if before_rank is not None and before_rank <= 5 and (
            after_rank is None or after_rank > 5
        ):
            lost_top5.append(cid)
        if before_rank is not None and after_rank is None:
            new_zero_candidate.append(cid)
    return {
        "previous_top1_lost": sorted(lost_top1),
        "previous_top3_lost": sorted(lost_top3),
        "previous_top5_lost": sorted(lost_top5),
        "new_positive_zero_candidate": sorted(new_zero_candidate),
    }


def _case_snapshot(report: dict, case_id: str) -> dict:
    for f in report.get("known_failures", []):
        if f["id"] == case_id:
            return {
                "rank": f.get("target_rank"),
                "score": f.get("target_score"),
                "higher_ranked": f.get("higher_ranked", []),
            }
    # top1 win or ambiguous pass: not a failure entry
    return {"rank": 1, "score": None, "higher_ranked": []}


def build_report(
    *,
    runtime_source_sha: str | None = None,
    fixture_sha256_baseline: str | None = None,
    baseline_commit: str | None = None,
) -> dict:
    baseline_evidence = json.loads(
        _BASELINE_EVIDENCE.read_text(encoding="utf-8")
    )
    before_failures, before_metrics = _baseline_maps(baseline_evidence)

    fixture = _load_fixture()
    after = evaluate(fixture=fixture, evaluated_sha=runtime_source_sha or _git_sha())
    # known_failures only lists positive misses; every other positive case is
    # a top1 win. case_type always comes from the fixture (failure entries
    # don't carry it).
    after_failures = {f["id"]: f for f in after.get("known_failures", [])}
    after_results = {}
    for case in fixture["cases"]:
        cid = case["id"]
        failure = after_failures.get(cid)
        after_results[cid] = {
            "id": cid,
            "case_type": case["case_type"],
            "target_rank": (
                failure.get("target_rank")
                if failure
                else (1 if case["case_type"] in _POSITIVE_TYPES else None)
            ),
        }

    fixture_sha_after = _sha256_file(_FIXTURE)
    if fixture_sha256_baseline is None and baseline_commit:
        fixture_sha256_baseline = _fixture_sha256_at(baseline_commit)

    report = {
        "task_id": "DAVI-MCP-DISCOVERY-QUALITY-CORRECTIVE-001",
        "runtime_source_sha": runtime_source_sha or _git_sha(),
        "benchmark_version": fixture.get("benchmark_version"),
        "provenance": {
            "fixture_sha256_before": fixture_sha256_baseline,
            "fixture_sha256_after": fixture_sha_after,
            "fixture_unchanged": (
                fixture_sha256_baseline is None
                or fixture_sha256_baseline == fixture_sha_after
            ),
            "runner_sha256": _sha256_file(Path(__file__).resolve()),
            "baseline_evaluated_sha": baseline_evidence.get("evaluated_sha"),
            "baseline_evidence": _BASELINE_EVIDENCE.name,
        },
        "allowlist": {
            "version_before": baseline_evidence.get("allowlist_version"),
            "version_after": after.get("allowlist_version"),
            "governed_operation_count": after.get("catalog_parity", {}).get(
                "allowlist_count"
            ),
        },
        "catalog_parity": after.get("catalog_parity"),
        "dq_stock_001": {
            "before": _case_snapshot(baseline_evidence, _CASE_ID),
            "after": _case_snapshot(after, _CASE_ID),
        },
        "metrics_before": before_metrics,
        "metrics_after": after.get("metrics"),
        "metric_deltas": {
            k: round(
                (after["metrics"].get(k) or 0) - (before_metrics.get(k) or 0), 4
            )
            for k in (
                "top1_accuracy",
                "top1_required_accuracy",
                "top3_recall",
                "top5_recall",
                "mrr",
                "positive_no_candidate_rate",
                "hard_negative_zero_candidate_rate",
                "unsupported_zero_candidate_rate",
                "ambiguous_top3_coverage",
                "ambiguous_top5_coverage",
                "unrelated_family_top1",
            )
        },
        "root_cause_before": baseline_evidence.get("root_cause_breakdown", {}),
        "root_cause_after": after.get("root_cause_breakdown", {}),
        "regressions": _regression_matrix(
            before_failures, after_results, after
        ),
        "known_failures_after": after.get("known_failures", []),
        "negative_detail": after.get("negative_detail"),
        "discover_contract_checks": after.get("discover_contract_checks"),
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="persist evidence JSON")
    parser.add_argument("--runtime-source-sha", default=None)
    parser.add_argument("--fixture-sha256-baseline", default=None)
    parser.add_argument("--baseline-commit", default=None)
    args = parser.parse_args()

    report = build_report(
        runtime_source_sha=args.runtime_source_sha,
        fixture_sha256_baseline=args.fixture_sha256_baseline,
        baseline_commit=args.baseline_commit,
    )
    ma = report["metrics_after"]
    print(json.dumps({
        "top1_accuracy": ma["top1_accuracy"],
        "top1_required_accuracy": ma["top1_required_accuracy"],
        "top3_recall": ma["top3_recall"],
        "top5_recall": ma["top5_recall"],
        "mrr": ma["mrr"],
        "positive_no_candidate_rate": ma["positive_no_candidate_rate"],
        "hard_negative_zero_candidate_rate": ma["hard_negative_zero_candidate_rate"],
        "unsupported_zero_candidate_rate": ma["unsupported_zero_candidate_rate"],
        "ambiguous_top3_coverage": ma["ambiguous_top3_coverage"],
        "ambiguous_top5_coverage": ma["ambiguous_top5_coverage"],
        "unrelated_family_top1": ma["unrelated_family_top1"],
    }, indent=2))
    print("family_metrics:", json.dumps(ma["family_metrics"], ensure_ascii=False))
    print("regressions:", json.dumps(report["regressions"], ensure_ascii=False))
    print("dq_stock_001:", json.dumps(report["dq_stock_001"], ensure_ascii=False))
    print("failures:", len(report["known_failures_after"]))
    if args.write:
        _EVIDENCE.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"evidence written: {_EVIDENCE.relative_to(_API_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
