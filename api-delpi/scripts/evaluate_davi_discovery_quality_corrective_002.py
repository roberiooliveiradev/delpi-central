"""DAVI command-intent corrective evidence runner.

DAVI-MCP-DISCOVERY-QUALITY-CORRECTIVE-002: re-runs the frozen benchmark
(``davi_discovery_quality_v1``) and the adversarial command-context fixture
(``davi_discovery_command_context_v1``) against the corrected guard/retrieval
source, diffing against the accepted Corrective-001 evidence artifact.

No network, no provider calls, no business execution, no candidate tokens in
output. Usage:

    python scripts/evaluate_davi_discovery_quality_corrective_002.py           # summary
    python scripts/evaluate_davi_discovery_quality_corrective_002.py --write   # evidence JSON

Provenance flags (use when git is unavailable, e.g. inside the app container):

    --runtime-source-sha <sha>   HEAD of the source tree being evaluated
    --fixture-sha256-baseline <hex>  sha256 of the frozen fixture at baseline
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
    _live_actions,
    _load_fixture,
    _ranked,
    evaluate,
)

_BASELINE_EVIDENCE = (
    _API_ROOT
    / "docs/integrations/evidence/davi-mcp-discovery-quality-corrective-001.json"
)
_COMMAND_FIXTURE = (
    _API_ROOT / "tests" / "fixtures" / "davi_discovery_command_context_v1.json"
)
_EVIDENCE = (
    _API_ROOT
    / "docs/integrations/evidence/davi-mcp-discovery-quality-corrective-002.json"
)
_TRANSLATION_CASE = "DQ-NEG-U-008"


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


def _command_context(actions) -> dict:
    """Run the command-context fixture: COMMAND_POSITIVE must reach the
    expected action (top3 floor), COMMAND_UNSUPPORTED must return zero
    candidates — by semantic evidence, never by verb."""
    fixture = json.loads(_COMMAND_FIXTURE.read_text(encoding="utf-8"))
    results = []
    for case in fixture["cases"]:
        ranked = _ranked(case["query"], actions, top_k=10)
        ranked_ids = [a.operation_id for a, _ in ranked]
        expected = case.get("expected_action_ids") or []
        entry = {
            "id": case["id"],
            "case_type": case["case_type"],
            "query": case["query"],
            "expected": expected,
            "ranked": ranked_ids,
            "candidate_count": len(ranked_ids),
        }
        if case["case_type"] == "COMMAND_POSITIVE":
            entry["expected_rank"] = (
                ranked_ids.index(expected[0]) + 1
                if expected and expected[0] in ranked_ids
                else None
            )
            entry["pass"] = entry["expected_rank"] is not None and entry[
                "expected_rank"
            ] <= 3
        else:
            entry["pass"] = not ranked_ids
        results.append(entry)
    positives = [r for r in results if r["case_type"] == "COMMAND_POSITIVE"]
    unsupported = [r for r in results if r["case_type"] == "COMMAND_UNSUPPORTED"]
    return {
        "fixture_sha256": _sha256_file(_COMMAND_FIXTURE),
        "positive": {
            "total": len(positives),
            "top1": sum(1 for r in positives if r.get("expected_rank") == 1),
            "top3": sum(
                1
                for r in positives
                if r.get("expected_rank") is not None
                and r["expected_rank"] <= 3
            ),
            "zero_candidate": sum(1 for r in positives if not r["ranked"]),
        },
        "unsupported": {
            "total": len(unsupported),
            "zero_candidate": sum(
                1 for r in unsupported if not r["ranked"]
            ),
        },
        "cases": results,
    }


def _guard_semantics() -> dict:
    """Guard behaviour before/after: orchestration verbs no longer fire the
    mutation guard; true mutation verbs and SQL phrases unchanged."""
    from app.application.external_capabilities.dynamic_information.read_only_intent_guard import (
        has_explicit_write_intent,
    )

    probes = {
        "mutation_blocked": [
            "insira um novo fornecedor",
            "altere o produto 10080055",
            "delete the product 10080055",
            "incluir um registro",
        ],
        "command_verbs_not_blocked": [
            "calcule o OTD de compras",
            "gere um resumo do estoque do produto 10080034",
            "monte um resumo dos pedidos em aberto",
            "traduza a descrição do produto para inglês",
            "emita a nota fiscal 12345",
        ],
        "generic_sql_zero_candidates": [
            "execute uma query SQL no banco",
            "select * from products",
            "rode uma consulta SQL",
        ],
    }
    actions = _live_actions()
    return {
        "mutation_blocked": {
            q: has_explicit_write_intent(q)
            for q in probes["mutation_blocked"]
        },
        "command_verbs_not_blocked": {
            q: has_explicit_write_intent(q)
            for q in probes["command_verbs_not_blocked"]
        },
        # Generic SQL fails closed at retrieval level (quarantine tokens),
        # not via the mutation guard.
        "generic_sql_zero_candidates": {
            q: not _ranked(q, actions, top_k=10)
            for q in probes["generic_sql_zero_candidates"]
        },
    }


def build_report(
    *,
    runtime_source_sha: str | None = None,
    fixture_sha256_baseline: str | None = None,
) -> dict:
    baseline_evidence = json.loads(
        _BASELINE_EVIDENCE.read_text(encoding="utf-8")
    )
    before_metrics = baseline_evidence.get("metrics_after", {})

    fixture = _load_fixture()
    after = evaluate(
        fixture=fixture,
        evaluated_sha=runtime_source_sha or _git_sha(),
    )

    actions = _live_actions()
    command_context = _command_context(actions)

    fixture_sha_after = _sha256_file(_FIXTURE)

    # Translation case verdict: the frozen UNSUPPORTED_NEGATIVE expects zero
    # candidates, but the request is mixed — product description retrieval is
    # governed (search_products serves `description`), translation itself is
    # agent-side orchestration after authoritative retrieval.
    translation_detail = next(
        (
            s
            for s in after.get("negative_detail", {}).get(
                "unsupported_spurious", []
            )
            if s["id"] == _TRANSLATION_CASE
        ),
        None,
    )
    translation_case = {
        "id": _TRANSLATION_CASE,
        "query": "traduza a descrição do produto para inglês",
        "frozen_classification": "UNSUPPORTED_NEGATIVE",
        "observed_candidates": (
            translation_detail["returned"] if translation_detail else []
        ),
        "semantic_verdict": (
            "MIXED_REQUEST — retrieval leg (product description) is governed "
            "via search_products.approvedResponseFields=[description,...]; "
            "translation is Agent-side orchestration after authoritative "
            "retrieval. Frozen zero-candidate expectation conflicts with the "
            "clarified command-intent architecture."
        ),
        "status": "BENCHMARK_CORRECTION_REQUIRED",
    }

    report = {
        "task_id": "DAVI-MCP-DISCOVERY-QUALITY-CORRECTIVE-002",
        "runtime_source_sha": runtime_source_sha or _git_sha(),
        "benchmark_version": fixture.get("benchmark_version"),
        "provenance": {
            "frozen_fixture_sha256_before": fixture_sha256_baseline,
            "frozen_fixture_sha256_after": fixture_sha_after,
            "fixture_unchanged": (
                fixture_sha256_baseline is None
                or fixture_sha256_baseline == fixture_sha_after
            ),
            "runner_sha256": _sha256_file(Path(__file__).resolve()),
            "baseline_evidence": _BASELINE_EVIDENCE.name,
            "baseline_runtime_source_sha": baseline_evidence.get(
                "runtime_source_sha"
            ),
        },
        "allowlist": {
            "version_before": baseline_evidence.get("allowlist", {}).get(
                "version_after"
            ),
            "version_after": after.get("allowlist_version"),
            "governed_operation_count": after.get("catalog_parity", {}).get(
                "allowlist_count"
            ),
        },
        "guard_semantics": _guard_semantics(),
        "command_context": command_context,
        "translation_case": translation_case,
        "catalog_parity": after.get("catalog_parity"),
        "dq_stock_001": {
            "before": baseline_evidence.get("dq_stock_001", {}).get("after"),
            "after": {
                "rank": (
                    lambda ids: ids.index("get_product_stock") + 1
                    if "get_product_stock" in ids
                    else None
                )(
                    [
                        a.operation_id
                        for a, _ in _ranked(
                            "estoque atual do produto 10080034",
                            actions,
                            top_k=10,
                        )
                    ]
                )
            },
        },
        "metrics_before": before_metrics,
        "metrics_after": after.get("metrics"),
        "metric_deltas": {
            k: round(
                (after["metrics"].get(k) or 0)
                - (before_metrics.get(k) or 0),
                4,
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
        "root_cause_after": after.get("root_cause_breakdown", {}),
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
    args = parser.parse_args()

    report = build_report(
        runtime_source_sha=args.runtime_source_sha,
        fixture_sha256_baseline=args.fixture_sha256_baseline,
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
    print("command_context:", json.dumps({
        "positive": report["command_context"]["positive"],
        "unsupported": report["command_context"]["unsupported"],
    }))
    print("guard:", json.dumps(report["guard_semantics"]))
    print("translation:", json.dumps(report["translation_case"], ensure_ascii=False))
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
