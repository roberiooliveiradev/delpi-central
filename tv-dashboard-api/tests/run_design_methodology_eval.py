"""PHASE 5 corpus runner — prints raw per-case results for baseline/candidate.

Usage (in-repo venv):
    .venv/bin/python tests/run_design_methodology_eval.py [--candidate]

Baseline mode (--candidate absent): records what the legacy path produces
(semantic_digest + visual_recommendation) and whether readiness machinery
exists. Candidate mode evaluates DesignIntelligenceService.evaluate_methodology.
"""

from __future__ import annotations

import json
import sys

sys.path.insert(0, ".")

from tests.design_methodology_corpus import CORPUS  # noqa: E402

from tv_app.application.services.data.design_intelligence_service import (  # noqa: E402
    DesignIntelligenceService,
)


def _baseline_case(case: dict) -> dict:
    fx = case["fixture"]
    out = {"id": case["id"], "mode": "baseline"}
    rows = fx.get("rows")
    if isinstance(rows, list):
        digest = DesignIntelligenceService.semantic_digest(rows, columns=fx.get("columns"))
        rec = DesignIntelligenceService.visual_recommendation(digest)
        out.update(
            {
                "recommendedType": rec.get("recommendedType"),
                "numeric_confidence_emitted": isinstance(rec.get("confidence"), float),
                "readiness": None,
                "read_before_ask": False,
                "missingFacts": None,
                "fabricated": rows == [] and bool(rec.get("recommendedType")),
            }
        )
    else:
        out.update(
            {
                "recommendedType": None,
                "readiness": None,
                "read_before_ask": False,
                "missingFacts": None,
                "fabricated": False,
            }
        )
    return out


def _candidate_case(case: dict) -> dict:
    fx = case["fixture"]
    out = {"id": case["id"], "mode": "candidate"}
    digest = None
    preview_error = None
    if isinstance(fx.get("rows"), list):
        digest = DesignIntelligenceService.semantic_digest(
            fx["rows"], columns=fx.get("columns")
        )
    elif fx.get("preview_error"):
        preview_error = fx["preview_error"]
    selection = fx.get("selection") or {}
    result = DesignIntelligenceService.evaluate_methodology(
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
        preview_error=preview_error,
    )
    out["result"] = result
    out["readiness"] = result.get("readiness")
    out["fabricated"] = bool(result.get("_fabricated"))
    return out


def main() -> None:
    candidate = "--candidate" in sys.argv
    results = [(_candidate_case(c) if candidate else _baseline_case(c)) for c in CORPUS]
    print(json.dumps(results, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
