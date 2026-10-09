"""P7 unified eval runner — one deterministic entry point over frozen corpora.

Usage: PYTHONPATH=. python tests/run_vista_eval.py

Computes corpus-native metrics against the FROZEN P5/P6 fixtures (same
semantics as their phase runners — no copied cases) and reports
suite-native metrics as delegated gates. Raw counts only — no composite
score, no fabricated percentages.
"""

from __future__ import annotations

import json
import sys

from tv_app.application.services.data.design_intelligence_service import (
    DesignIntelligenceService,
)
from tests.design_methodology_corpus import CORPUS as P5_CORPUS
from tests.run_solution_intelligence_eval import evaluate_case as p6_evaluate
from tests.solution_intelligence_corpus import (
    FORBIDDEN_CANDIDATE_FIELDS,
    P6_CORPUS,
)
from tests.vista_metric_catalog import EVAL_CORPUS_VERSION, VISTA_METRIC_CATALOG


# --- P5 corpus evaluation (same expectation semantics as the P5 pytest) ---

_P5_DIM_BY_EXPECT_KEY = {
    "family_in": "VISUAL_SELECTION",
    "family_not_in": "VISUAL_SELECTION",
    "next_action": "CLARIFICATION_CORRECTNESS",
    "read_capability_in": "CLARIFICATION_CORRECTNESS",
    "next_question_only_for": "CLARIFICATION_CORRECTNESS",
    "no_target_guess": "TARGET_RESOLUTION",
    "target_id": "TARGET_RESOLUTION",
    "evidence_level_in": "VISUAL_EVIDENCE_CORRECTNESS",
    "aesthetic_claim_blocked_without_pixels": "VISUAL_EVIDENCE_CORRECTNESS",
    "fabricated": "UNSUPPORTED_CLAIM",
    "readiness": "DATA_SHAPE_AWARENESS",
    "readiness_in": "DATA_SHAPE_AWARENESS",
    "missing_fact": "DATA_SHAPE_AWARENESS",
}


def _p5_eval(case: dict) -> dict:
    fx = case["fixture"]
    digest = None
    if isinstance(fx.get("rows"), list):
        digest = DesignIntelligenceService.semantic_digest(
            fx["rows"], columns=fx.get("columns")
        )
    selection = fx.get("selection") or {}
    return DesignIntelligenceService.evaluate_methodology(
        intent=case["intent"],
        digest=digest,
        design_audit=fx.get("audit"),
        selected_objects=selection.get("selectedObjects") or [],
        missing_ids=selection.get("missingIds") or [],
        selection_state=selection.get("selectionState"),
        canonical_pixels=fx.get("pixels"),
        extra_missing_readable=fx.get("missing_readable") or [],
        extra_missing_user=fx.get("missing_user") or [],
        has_data_source=bool(fx.get("has_data_source")),
        explicit_user_choice=fx.get("explicit_choice"),
        dominant_family=fx.get("dominant_family"),
        preview_error=fx.get("preview_error"),
    )


def _p5_case_ok(case: dict) -> bool:
    """Single deterministic verdict per case (all expectations must hold)."""
    result = _p5_eval(case)
    exp = case["expect"]
    strategy = result.get("strategy") or {}
    if "readiness" in exp and result["readiness"] != exp["readiness"]:
        return False
    if "readiness_in" in exp and result["readiness"] not in exp["readiness_in"]:
        return False
    if "family_in" in exp and strategy.get("visualFamily") not in exp["family_in"]:
        return False
    if "family_not_in" in exp:
        chosen = {strategy.get("visualFamily")}
        if chosen & exp["family_not_in"]:
            return False
    if exp.get("fabricated") is False and result.get("_fabricated") is not False:
        return False
    if exp.get("next_action") == "READ":
        if result["sufficiency"] != "READ_MORE_STATE":
            return False
        if (result.get("nextAction") or {}).get("kind") != "READ":
            return False
    if "read_capability_in" in exp:
        cap = (result.get("nextAction") or {}).get("capability")
        if cap not in exp["read_capability_in"]:
            return False
    if exp.get("next_question_only_for"):
        if (result.get("nextQuestion") or {}).get("fact") != exp["next_question_only_for"]:
            return False
    if exp.get("missing_fact") and not any(
        m["fact"] == exp["missing_fact"] for m in result["missingFacts"]
    ):
        return False
    if exp.get("no_target_guess") and (
        result["facts"].get("target_object") or {}
    ).get("value"):
        return False
    if exp.get("target_id") and result["facts"]["target_object"]["value"] != exp[
        "target_id"
    ]:
        return False
    if "evidence_level_in" in exp and result["evidence"]["level"] not in exp[
        "evidence_level_in"
    ]:
        return False
    if exp.get("aesthetic_claim_blocked_without_pixels"):
        if result["evidence"]["level"] in {"PIXELS_INSPECTED", "HUMAN_JUDGMENT"}:
            return False
        if result.get("aestheticGate") != "PIXELS_REQUIRED_FOR_AESTHETIC_CLAIMS":
            return False
    if exp.get("explicit_choice_preserved"):
        choice = strategy.get("explicitUserChoice") or {}
        if not choice.get("respected"):
            return False
        if choice.get("visualFamily") != case["fixture"]["explicit_choice"]:
            return False
    return True


def _p6_case_ok(case: dict, row: dict) -> bool:
    exp = case["expect"]
    if row["raised"] or not row["miss_invariant"]:
        return False
    if "core_calls" in exp and row["core_calls"] != exp["core_calls"]:
        return False
    if "gap" in exp and row["gap"] != exp["gap"]:
        return False
    if "gap_in" in exp and row["gap"] not in exp["gap_in"]:
        return False
    if "candidates" in exp and sorted(row["candidates"]) != sorted(
        exp["candidates"]
    ):
        return False
    if any(k in FORBIDDEN_CANDIDATE_FIELDS for k in row["candidate_keys"]):
        return False
    return True


def _count(cases, ok):
    return {"passed": sum(1 for c in cases if ok(c)), "total": len(cases)}


def run() -> dict:
    # --- P5 corpus-native dims -------------------------------------------
    p5_rows = {c["id"]: _p5_case_ok(c) for c in P5_CORPUS}
    p5_dim_rows: dict[str, dict[str, int]] = {}
    for case in P5_CORPUS:
        dims = {
            _P5_DIM_BY_EXPECT_KEY[k]
            for k in case["expect"]
            if k in _P5_DIM_BY_EXPECT_KEY
        }
        # every case contributes to DATA_SHAPE_AWARENESS via readiness
        for dim in dims or {"DATA_SHAPE_AWARENESS"}:
            row = p5_dim_rows.setdefault(dim, {"passed": 0, "total": 0})
            row["total"] += 1
            row["passed"] += int(p5_rows[case["id"]])

    # --- P6 corpus-native dims ---------------------------------------------
    p6_rows = {c["id"]: p6_evaluate(c) for c in P6_CORPUS}
    p6_hits = [c for c in P6_CORPUS if c["tv_routes"]]
    p6_misses = [c for c in P6_CORPUS if not c["tv_routes"]]
    p6_dim_rows = {
        "DATA_ROUTE_RETRIEVAL": _count(
            p6_hits, lambda c: p6_rows[c["id"]]["gap"] == "TV_ROUTE_FOUND"
        ),
        "FALSE_ABSENCE": _count(
            p6_misses,
            lambda c: p6_rows[c["id"]]["miss_invariant"]
            and p6_rows[c["id"]]["gap"] is not None,
        ),
        "SOLUTION_OWNER_RESOLUTION": _count(
            [c for c in P6_CORPUS if "candidates" in c["expect"]],
            lambda c: sorted(p6_rows[c["id"]]["candidates"])
            == sorted(c["expect"]["candidates"]),
        ),
        "ROUTE_VS_SOLUTION_DISTINCTION": _count(
            P6_CORPUS,
            lambda c: (
                p6_rows[c["id"]]["gap"] == c["expect"].get("gap")
                if "gap" in c["expect"]
                else p6_rows[c["id"]]["gap"] in (c["expect"].get("gap_in") or [])
            ),
        ),
        "AMBIGUITY_HANDLING": _count(
            [c for c in P6_CORPUS if c["id"] in {"miss_ambiguous", "miss_mixed_access"}],
            lambda c: p6_rows[c["id"]]["gap"] == "AMBIGUOUS_SOLUTIONS",
        ),
        "UNAUTHORIZED_SOLUTION_LEAK": _count(
            [c for c in P6_CORPUS if "candidates" in c["expect"]],
            lambda c: not any(
                k in FORBIDDEN_CANDIDATE_FIELDS
                for k in p6_rows[c["id"]]["candidate_keys"]
            ),
        ),
    }

    metrics: dict[str, dict] = {}
    for dim_id, meta in VISTA_METRIC_CATALOG.items():
        entry = {"status": meta["status"], "source": meta["measurementSource"]}
        if dim_id in p5_dim_rows:
            entry.update(p5_dim_rows[dim_id])
        elif dim_id in p6_dim_rows:
            entry.update(p6_dim_rows[dim_id])
        else:
            entry["delegated"] = meta["measurementSource"].startswith("suite:")
            entry["passed"] = None
            entry["total"] = None
        metrics[dim_id] = entry

    report = {
        "corpusVersion": EVAL_CORPUS_VERSION,
        "metrics": metrics,
    }
    print(json.dumps(report, indent=1, sort_keys=True))
    return report


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
