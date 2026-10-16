"""P7 residual closure — DATA_DIAGNOSIS corpus integrity + eval tests.

Proves the frozen corpus is deterministic, closed-vocabulary, owner-backed,
and free of business payloads; and that every case evaluates through its
canonical owner against the frozen expectation (baseline measurement).
"""

import pytest

from tests.data_diagnosis_corpus import (
    DATA_DIAGNOSIS_CORPUS,
    DATA_DIAGNOSIS_CORPUS_VERSION,
    DIAGNOSIS_VOCABULARY,
    NEXT_STEP_ALLOWED,
    NEXT_STEP_VOCABULARY,
)
from tests.data_diagnosis_eval import evaluate_all, evaluate_case
from tests.run_vista_eval import run as run_unified_eval


# --- corpus integrity ------------------------------------------------------


def test_case_ids_unique():
    ids = [c["caseId"] for c in DATA_DIAGNOSIS_CORPUS]
    assert len(ids) == len(set(ids))


def test_expected_vocabulary_closed():
    for case in DATA_DIAGNOSIS_CORPUS:
        assert case["expect"]["diagnosis"] in DIAGNOSIS_VOCABULARY
        assert case["expect"]["next_step"] in NEXT_STEP_VOCABULARY


def test_next_step_consistent_with_diagnosis():
    for case in DATA_DIAGNOSIS_CORPUS:
        allowed = NEXT_STEP_ALLOWED[case["expect"]["diagnosis"]]
        assert case["expect"]["next_step"] in allowed


def test_every_case_has_authoritative_source():
    for case in DATA_DIAGNOSIS_CORPUS:
        assert case["authoritativeSource"].strip()
        assert case["kind"] in {
            "preview",
            "binding",
            "model",
            "filter_digest",
            "route_miss",
            "cross_boundary",
        }


def test_no_sensitive_business_payload():
    """Fixtures are synthetic: no identity, tokens, or real business rows."""
    forbidden = ("jwt", "token", "password", "email", "cpf", "authorization")
    for case in DATA_DIAGNOSIS_CORPUS:
        text = repr(case["fixture"]).lower()
        for marker in forbidden:
            assert marker not in text, f"{case['caseId']} carries {marker}"


def test_expected_codes_are_canonical():
    """No orphan expected codes: every asserted code exists in an owner."""
    canonical = {
        None,
        "PARAM_REQUIRED",
        "PARAM_INVALID",
        "DATA_BINDING_FIELD_MISSING",
        "RESOURCE_NOT_FOUND",
        "DATA_RESOLUTION_FAILED",
        "m.merge_source_unavailable",
    }
    for case in DATA_DIAGNOSIS_CORPUS:
        assert case["expect"].get("code") in canonical


def test_denominator_deterministic():
    assert len(DATA_DIAGNOSIS_CORPUS) == 12
    assert DATA_DIAGNOSIS_CORPUS_VERSION == "data-diagnosis-v1"


def test_required_categories_covered():
    cats = {c["category"] for c in DATA_DIAGNOSIS_CORPUS}
    required = {
        "healthy_runtime",
        "empty_data",
        "param_validation",
        "binding_contract",
        "datamodel_lookup",
        "transform_failure",
        "runtime_failure",
        "filter_effect",
        "filter_layering",
        "route_discovery_gap",
        "cross_boundary",
    }
    assert required <= cats


# --- eval (baseline) --------------------------------------------------------


@pytest.mark.parametrize(
    "case", DATA_DIAGNOSIS_CORPUS, ids=[c["caseId"] for c in DATA_DIAGNOSIS_CORPUS]
)
def test_case_matches_frozen_expectation(case):
    result = evaluate_case(case)
    assert result["ok"], (
        f"{case['caseId']}: expected {result['expected']} got "
        f"{result['observed']} ({result['observedCode']}) flags={result['failures']}"
    )


def test_baseline_aggregate():
    report = evaluate_all()
    assert report["total"] == 12
    assert report["passed"] == 12
    assert report["safety"] == {
        "FALSE_EMPTY_AS_ERROR": 0,
        "FALSE_ERROR_AS_EMPTY": 0,
        "FALSE_ABSENCE": 0,
        "UNTYPED_ERROR": 0,
        "WRONG_NEXT_STEP": 0,
    }


def test_unified_runner_reports_data_diagnosis():
    report = run_unified_eval()
    dd = report["metrics"]["DATA_DIAGNOSIS"]
    assert dd["status"] == "MEASURABLE_NOW"
    assert dd["passed"] == 12 and dd["total"] == 12
    assert dd["safety"]["FALSE_EMPTY_AS_ERROR"] == 0
    assert dd["safety"]["FALSE_ERROR_AS_EMPTY"] == 0
    assert dd["safety"]["FALSE_ABSENCE"] == 0
    assert dd["safety"]["UNTYPED_ERROR"] == 0
    assert dd["safety"]["WRONG_NEXT_STEP"] == 0
