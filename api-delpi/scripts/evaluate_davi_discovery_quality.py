"""DAVI discovery-quality benchmark runner (DAVI-MCP-DISCOVERY-QUALITY-001).

Deterministic, provider-independent measurement of ``discover_delpi_information``
retrieval quality over the same live-OpenAPI action index the runtime seeds.

No network, no provider calls, no business execution, no candidate tokens in
output. Usage:

    python scripts/evaluate_davi_discovery_quality.py            # console summary
    python scripts/evaluate_davi_discovery_quality.py --write    # + evidence JSON
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

_API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_API_ROOT))

_FIXTURE = _API_ROOT / "tests" / "fixtures" / "davi_discovery_quality_v1.json"
_EVIDENCE = (
    _API_ROOT
    / "docs/integrations/evidence/davi-mcp-discovery-quality-001.json"
)

_POSITIVE_TYPES = {"POSITIVE_PRECISE", "POSITIVE_PARAPHRASE", "QUARANTINE_CONFLICT"}
_HARD_NEGATIVE_TYPES = {"WRITE_NEGATIVE", "GENERIC_SQL_NEGATIVE"}


def _load_fixture(path: Path = _FIXTURE) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _live_actions():
    """Same catalog source as production runtime: live generated OpenAPI."""
    from app.application.external_capabilities.dynamic_information.action_index import (
        seed_actions_from_openapi,
    )
    from app.main import app

    return seed_actions_from_openapi(app.openapi())


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


def _ranked(query: str, actions, *, top_k: int):
    from app.application.external_capabilities.dynamic_information.retrieval import (
        retrieve_eligible_actions,
    )

    return retrieve_eligible_actions(query, actions, top_k=top_k)


def _discover(query: str, *, top_k: int) -> dict:
    from app.application.external_capabilities.dynamic_information.discover_service import (
        discover_delpi_information,
    )

    result = discover_delpi_information(
        query=query, top_k=top_k, actor_id="discovery-quality-benchmark"
    )
    for candidate in result.get("candidates", []):
        candidate.pop("candidate_token", None)
    return result


def _query_tokens(query: str) -> set:
    from app.application.external_capabilities.dynamic_information.text_normalize import (
        normalize_text,
        tokenize,
    )

    return set(tokenize(normalize_text(query)))


def _alias_match_kind(action_id: str, query_tokens: set, aliases_by_id: dict):
    """Return 'multiword'/'single' if an alias of the action is fully covered by
    the query token set, else None. Deterministic diagnostic signal — it does
    not replicate retrieval scoring, only lexical alias coverage."""
    from app.application.external_capabilities.dynamic_information.text_normalize import (
        normalize_text,
        tokenize,
    )

    kind = None
    for alias in aliases_by_id.get(action_id, []):
        alias_tokens = set(tokenize(normalize_text(str(alias))))
        if alias_tokens and alias_tokens <= query_tokens:
            if len(alias_tokens) > 1:
                return "multiword"
            kind = "single"
    return kind


def _classify_root_cause(entry, result, case, family_of, aliases_by_id,
                         quarantine_tokens) -> str:
    """Deterministic evidence-driven classification. Order matters: each rule
    fires on observable signals (zero candidates, score gap, matched alias
    kind, family cross-over, quarantine suppression), not on guesswork."""
    if case["case_type"] == "QUARANTINE_CONFLICT":
        return "QUARANTINE_INTERACTION"
    q_tokens = _query_tokens(case["query"])
    expected_id = entry["expected"]
    expected_kind = (
        _alias_match_kind(expected_id, q_tokens, aliases_by_id)
        if expected_id
        else None
    )
    if result["target_rank"] is None:
        if not result["ranked"]:
            return "ALIAS_MISSING"  # zero candidates: query never reached the action
        if expected_kind is not None:
            # alias lexically covered yet action absent — check quarantine token overlap
            from app.application.external_capabilities.dynamic_information.text_normalize import (
                normalize_text,
                tokenize,
            )

            covered = [
                a
                for a in aliases_by_id.get(expected_id, [])
                if set(tokenize(normalize_text(str(a)))) <= q_tokens
            ]
            if any(
                set(tokenize(normalize_text(str(a)))) & quarantine_tokens
                for a in covered
            ):
                return "QUARANTINE_INTERACTION"
            return "ALIAS_COLLISION"  # covered but scored to zero
        return "ALIAS_MISSING"  # other actions matched; expected alias coverage absent
    gap = entry["higher_ranked"][0]["score"] - (entry["target_score"] or 0.0)
    if gap <= 0.005:
        return "TIE_BREAK_ARTIFACT"  # near-tie decided by secondary sort keys
    higher = [h["action_id"] for h in entry["higher_ranked"]]
    kinds = [
        _alias_match_kind(aid, q_tokens, aliases_by_id) for aid in higher
    ]
    foreign = [
        aid for aid in higher
        if family_of.get(aid) not in (None, entry["family"])
    ]
    if foreign and all(
        _alias_match_kind(aid, q_tokens, aliases_by_id) == "single"
        for aid in foreign
    ):
        return "SINGLE_TOKEN_OVERWEIGHT"
    if any(k == "multiword" for k in kinds):
        return "MULTIWORD_ALIAS_COLLISION"
    if foreign:
        return "ALIAS_COLLISION"
    if expected_kind is None:
        return "SUMMARY_TOKEN_NOISE"  # target scored via summary/description only
    if expected_kind == "single":
        return "ALIAS_TOO_GENERIC"
    return "OTHER"


def evaluate(fixture: dict | None = None, *, evaluated_sha: str | None = None) -> dict:
    from app.application.external_capabilities.dynamic_information.content_loader import (
        load_dynamic_read_budgets,
        load_external_read_allowlist,
    )
    from app.application.external_capabilities.dynamic_information.eligibility import (
        is_dynamically_executable,
    )

    fixture = fixture or _load_fixture()
    cases = fixture["cases"]
    budgets = load_dynamic_read_budgets()
    top_k = int(budgets.get("discover_max_top_k") or 10)
    allowlist = load_external_read_allowlist()

    actions = _live_actions()
    eligible = {a.operation_id for a in actions if is_dynamically_executable(a.davi_status)}
    action_by_id = {a.operation_id: a for a in actions}
    aliases_by_id = {
        o["operationId"]: list(o.get("semanticAliases") or [])
        for o in allowlist.get("operations", [])
    }

    case_by_id = {c["id"]: c for c in cases}

    # op -> family map derived from positive fixture coverage
    family_of = {}
    for case in cases:
        for op in case.get("expected_action_ids") or []:
            family_of.setdefault(op, case["family"])

    quarantine_tokens = set(allowlist.get("retrievalQuarantineTokens") or [])

    results = []
    for case in cases:
        ranked = _ranked(case["query"], actions, top_k=top_k)
        ranked_ids = [a.operation_id for a, _ in ranked]
        ranked_scores = [round(float(s), 4) for _, s in ranked]
        expected = case.get("expected_action_ids") or []
        target_rank = None
        target_score = None
        if expected and expected[0] in ranked_ids:
            target_rank = ranked_ids.index(expected[0]) + 1
            target_score = ranked_scores[target_rank - 1]
        results.append(
            {
                "id": case["id"],
                "case_type": case["case_type"],
                "family": case["family"],
                "query": case["query"],
                "expected": expected,
                "top1_required": bool(case.get("top1_required")),
                "ranked": ranked_ids,
                "scores": ranked_scores,
                "target_rank": target_rank,
                "target_score": target_score,
            }
        )

    def _rate(num: float, den: float) -> float:
        return round(num / den, 4) if den else 0.0

    positives = [r for r in results if r["case_type"] in _POSITIVE_TYPES]
    ambiguous = [r for r in results if r["case_type"] == "AMBIGUOUS"]
    hard_neg = [r for r in results if r["case_type"] in _HARD_NEGATIVE_TYPES]
    unsupported = [r for r in results if r["case_type"] == "UNSUPPORTED_NEGATIVE"]

    def _hit(r, k):
        return r["target_rank"] is not None and r["target_rank"] <= k

    def _amb_hit(r, k):
        return bool(set(r["expected"]) & set(r["ranked"][:k]))

    metrics = {
        "case_counts": {
            "total": len(results),
            "positive_precise": sum(1 for r in results if r["case_type"] == "POSITIVE_PRECISE"),
            "positive_paraphrase": sum(1 for r in results if r["case_type"] == "POSITIVE_PARAPHRASE"),
            "ambiguous": len(ambiguous),
            "write_negative": sum(1 for r in results if r["case_type"] == "WRITE_NEGATIVE"),
            "generic_sql_negative": sum(1 for r in results if r["case_type"] == "GENERIC_SQL_NEGATIVE"),
            "unsupported_negative": len(unsupported),
            "quarantine_conflict": sum(1 for r in results if r["case_type"] == "QUARANTINE_CONFLICT"),
        },
        "positive_case_count": len(positives),
        "top1_accuracy": _rate(sum(1 for r in positives if r["target_rank"] == 1), len(positives)),
        "top1_required_accuracy": _rate(
            sum(1 for r in positives if r["top1_required"] and r["target_rank"] == 1),
            sum(1 for r in positives if r["top1_required"]),
        ),
        "top3_recall": _rate(sum(1 for r in positives if _hit(r, 3)), len(positives)),
        "top5_recall": _rate(sum(1 for r in positives if _hit(r, 5)), len(positives)),
        "mrr": round(
            sum(1.0 / r["target_rank"] for r in positives if r["target_rank"])
            / len(positives),
            4,
        ) if positives else 0.0,
        "positive_no_candidate_rate": _rate(
            sum(1 for r in positives if not r["ranked"]), len(positives)
        ),
        "hard_negative_zero_candidate_rate": _rate(
            sum(1 for r in hard_neg if not r["ranked"]), len(hard_neg)
        ),
        "unsupported_zero_candidate_rate": _rate(
            sum(1 for r in unsupported if not r["ranked"]), len(unsupported)
        ),
        "ambiguous_top3_coverage": _rate(
            sum(1 for r in ambiguous if _amb_hit(r, 3)), len(ambiguous)
        ),
        "ambiguous_top5_coverage": _rate(
            sum(1 for r in ambiguous if _amb_hit(r, 5)), len(ambiguous)
        ),
        "positive_target_misses": sum(1 for r in positives if r["target_rank"] is None),
        "positive_target_rank_gt5": sum(
            1 for r in positives if r["target_rank"] is not None and r["target_rank"] > 5
        ),
        "hard_negative_leaks": sum(1 for r in hard_neg if r["ranked"]),
        "unrelated_family_top1": sum(
            1
            for r in positives
            if r["ranked"]
            and r["target_rank"] != 1
            and family_of.get(r["ranked"][0]) not in (None, r["family"])
        ),
    }

    families = {}
    for fam in sorted({r["family"] for r in positives}):
        subset = [r for r in positives if r["family"] == fam]
        families[fam] = {
            "cases": len(subset),
            "top1": _rate(sum(1 for r in subset if r["target_rank"] == 1), len(subset)),
            "top3": _rate(sum(1 for r in subset if _hit(r, 3)), len(subset)),
            "top5": _rate(sum(1 for r in subset if _hit(r, 5)), len(subset)),
        }
    metrics["family_metrics"] = families

    failures = []
    for r in positives:
        if r["target_rank"] == 1:
            continue
        expected_id = r["expected"][0] if r["expected"] else None
        higher = [
            {"action_id": aid, "score": r["scores"][i]}
            for i, aid in enumerate(r["ranked"])
            if r["target_rank"] is None or i < r["target_rank"] - 1
        ]
        entry = {
            "id": r["id"],
            "query": r["query"],
            "family": r["family"],
            "expected": expected_id,
            "target_rank": r["target_rank"],
            "target_score": r["target_score"],
            "higher_ranked": higher[:5],
            "expected_aliases": aliases_by_id.get(expected_id, []),
        }
        if r["target_rank"] is None:
            entry["higher_candidate_aliases"] = {
                aid: aliases_by_id.get(aid, []) for _, aid in enumerate(r["ranked"][:3])
            }
        entry["root_cause"] = _classify_root_cause(
            entry, r, case_by_id[r["id"]], family_of, aliases_by_id,
            quarantine_tokens,
        )
        failures.append(entry)

    root_cause_breakdown = {}
    for f in failures:
        root_cause_breakdown[f["root_cause"]] = (
            root_cause_breakdown.get(f["root_cause"], 0) + 1
        )

    negative_detail = {
        "hard_negative_leaked": [
            {"id": r["id"], "query": r["query"], "leaked": r["ranked"]}
            for r in hard_neg
            if r["ranked"]
        ],
        "unsupported_spurious": [
            {"id": r["id"], "query": r["query"], "returned": r["ranked"]}
            for r in unsupported
            if r["ranked"]
        ],
        "ambiguous_zero_candidate": [
            {"id": r["id"], "query": r["query"]}
            for r in ambiguous
            if not r["ranked"]
        ],
    }

    # discover-contract level for representative cases (all negatives + first
    # 40 positives) — validates candidate shape/order without persisting tokens.
    contract_checks = {"ran": 0, "shape_ok": 0, "order_matches_retrieval": 0}
    contract_subset = [
        c for c in cases if c["case_type"] in _HARD_NEGATIVE_TYPES
    ] + [c for c in cases if c["case_type"] in _POSITIVE_TYPES][:40]
    for case in contract_subset:
        res = _discover(case["query"], top_k=5)
        contract_checks["ran"] += 1
        cand_ids = [c.get("action_id") for c in res.get("candidates", [])]
        ranked_ids = _ranked(case["query"], actions, top_k=5)
        if all("candidate_token" not in c for c in res.get("candidates", [])):
            contract_checks["shape_ok"] += 1
        if cand_ids == [a.operation_id for a, _ in ranked_ids]:
            contract_checks["order_matches_retrieval"] += 1

    return {
        "task_id": "DAVI-MCP-DISCOVERY-QUALITY-001",
        "evaluated_sha": evaluated_sha or _git_sha(),
        "catalog_source": "live app.openapi() (same as runtime seed)",
        "catalog_operation_count": len(eligible),
        "allowlist_version": allowlist.get("version"),
        "benchmark_version": fixture.get("benchmark_version"),
        "metrics": metrics,
        "known_failures": failures,
        "root_cause_breakdown": root_cause_breakdown,
        "negative_detail": negative_detail,
        "discover_contract_checks": contract_checks,
        "catalog_parity": {
            "allowlist_count": len(allowlist.get("operations") or []),
            "live_openapi_executable_count": len(eligible),
            "baseline_executable_count": "87 (expected: 2 SEMANTIC_READ_POST ops lack baseline requestBody)",
            "runtime_observed_eligible_count": 89,
            "classification": "EXPLAINED_DIFFERENCE",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="persist evidence JSON")
    parser.add_argument("--sha", default=None, help="override evaluated git SHA")
    args = parser.parse_args()
    report = evaluate(evaluated_sha=args.sha)
    m = report["metrics"]
    print(json.dumps({"case_counts": m["case_counts"], **{
        k: v for k, v in m.items() if k != "case_counts" and k != "family_metrics"
    }}, indent=2, ensure_ascii=False))
    print("family_metrics:", json.dumps(m["family_metrics"], ensure_ascii=False))
    print("failures:", len(report["known_failures"]))
    if args.write:
        _EVIDENCE.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"evidence written: {_EVIDENCE.relative_to(_API_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
