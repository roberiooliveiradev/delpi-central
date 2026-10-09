"""Phase 6 — solution intelligence on TV route misses (roadmap §39/§40).

Corpus-driven contract tests plus security/boundary invariants:
- route hit → zero Core calls;
- miss → exactly one bounded Core lookup, typed gapClassification;
- user-parity: the caller's Bearer is forwarded, never substituted;
- candidates carry only the bounded safe projection — never executable
  identifiers, routes, permissions, or manifest internals;
- fail-closed CONTRACT_GAP on any Core failure — never a false absence.
"""

from __future__ import annotations

import pytest

from tests.solution_intelligence_corpus import (
    FORBIDDEN_CANDIDATE_FIELDS,
    P6_CORPUS,
)
from tests.run_solution_intelligence_eval import evaluate_case


# ---------------------------------------------------------------- corpus


@pytest.mark.parametrize("case", P6_CORPUS, ids=lambda c: c["id"])
def test_corpus_case(case):
    row = evaluate_case(case)
    expect = case["expect"]
    assert row["raised"] is False, f"{case['id']} raised: {row.get('error')}"
    assert row["miss_invariant"] is True

    if "core_calls" in expect:
        assert row["core_calls"] == expect["core_calls"]

    if "gap" in expect:
        assert row["gap"] == expect["gap"]
    elif "gap_in" in expect:
        assert row["gap"] in expect["gap_in"]

    if "candidates" in expect:
        assert sorted(row["candidates"]) == sorted(expect["candidates"])

    # No candidate may carry fields outside the bounded projection.
    for key in row["candidate_keys"]:
        assert key not in FORBIDDEN_CANDIDATE_FIELDS
    allowed = {"id", "name", "category", "accessible", "epistemic"}
    assert set(row["candidate_keys"]) <= allowed


def test_hit_never_calls_core():
    for case in P6_CORPUS:
        if case["tv_routes"]:
            row = evaluate_case(case)
            assert row["core_calls"] == 0


def test_miss_calls_core_at_most_once():
    for case in P6_CORPUS:
        if not case["tv_routes"]:
            row = evaluate_case(case)
            assert row["core_calls"] <= 1


def test_bearer_is_forwarded_not_substituted():
    for case in P6_CORPUS:
        if not case["tv_routes"] and case["core_result"] != "no_auth":
            row = evaluate_case(case)
            assert row["authorizations"] == ["Bearer user-token"]


def test_no_absence_language():
    row = evaluate_case(
        next(c for c in P6_CORPUS if c["id"] == "miss_no_evidence")
    )
    assert row["gap"] == "NO_SOLUTION_EVIDENCE"


# ------------------------------------------------- unit-level contracts


def test_ambiguous_order_deterministic():
    case = next(c for c in P6_CORPUS if c["id"] == "miss_ambiguous")
    first = evaluate_case(case)
    second = evaluate_case(case)
    assert first["candidates"] == second["candidates"]
    assert len(first["candidates"]) == 2


def test_gap_vocabulary_is_closed():
    from tv_app.application.services.solution_intelligence_service import (
        GAP_CLASSIFICATIONS,
        SolutionIntelligenceService,
    )

    out = SolutionIntelligenceService().classify("anything", [])
    assert out["gapClassification"] in GAP_CLASSIFICATIONS
    assert SolutionIntelligenceService.contract_gap()["gapClassification"] in (
        GAP_CLASSIFICATIONS
    )


def test_candidates_are_knowledge_not_executable():
    case = next(c for c in P6_CORPUS if c["id"] == "miss_one_solution")
    row = evaluate_case(case)
    for key in row["candidate_keys"]:
        # Candidates must never expose executable route identifiers.
        assert key not in {"operationId", "path", "url", "endpoint"}


# ------------------------------------------------------------- gateway


def test_gateway_drops_non_safe_fields():
    from tv_app.infrastructure.gateways.core_solution_catalog_gateway import (
        _project_solution,
    )

    projected = _project_solution(
        {
            "id": "commercial",
            "name": "Portal Comercial",
            "description": "desc",
            "category": "commercial",
            "accessible": True,
            "routes": [{"path": "/crm"}],
            "permissions": [{"code": "x.view"}],
            "dependencies": ["core-api"],
            "backend": {"host": "internal"},
        }
    )
    assert set(projected.keys()) == {
        "id",
        "name",
        "description",
        "category",
        "accessible",
    }


def test_gateway_rejects_invalid_item_shape():
    from tv_app.application.gpt_actions.errors import GptActionsError
    from tv_app.infrastructure.gateways.core_solution_catalog_gateway import (
        _project_solution,
    )

    with pytest.raises(GptActionsError):
        _project_solution("not-a-dict")
    with pytest.raises(GptActionsError):
        _project_solution({"name": "no-id"})
