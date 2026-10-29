"""Task 08 (DELIA-C3-PYDANTICAI-STRUCTURED-DECISION-AB-01): PydanticAI
vs baseline structured-output reliability — experiment-harness
invariants V1–V18.

The harness lives under ``delia-api/scripts/`` (isolated evaluation
boundary). These tests pin the corpus semantics, the equivalence of
the strict-pydantic validation arm, and the architectural constraints:
no SDK import under ``app/``, no hidden retries, no tool execution,
no authority drift, no production-code change.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
HARNESS_PATH = (
    REPO / "scripts" / "pydanticai_structured_output_eval.py"
)


def _load_harness():
    spec = importlib.util.spec_from_file_location(
        "pydanticai_structured_output_eval", HARNESS_PATH
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def harness():
    return _load_harness()


# ---------- V1–V6, V15–V16: corpus semantics through the harness ----------


def test_corpus_minimum_categories(harness):
    ids = {c.case_id for c in harness.CORPUS}
    for required in (
        "valid_selection",
        "malformed_json",
        "missing_required_field",
        "wrong_field_type",
        "invalid_enum",
        "extra_unexpected_properties",
        "non_object_output",
        "applicable_false_passthrough",
        "semantically_invalid_capability",
        "fenced_json",
    ):
        assert required in ids, f"corpus missing {required}"


def test_v1_valid_output_survives_both_arms(harness):
    case = next(c for c in harness.CORPUS if c.case_id == "valid_selection")
    base = harness.baseline_verdict(case.raw, expected=case.expected_fields)
    strict = harness.strict_verdict(case.raw, schema=case.schema_key)
    assert base.accepted is True
    assert strict.accepted is True
    # V15 parity: the typed proposal projects to the same contract.
    assert (
        strict.projected == base.projected
    ), "strict arm must preserve the existing proposal contract"


def test_v2_malformed_json_rejected_by_both(harness):
    case = next(c for c in harness.CORPUS if c.case_id == "malformed_json")
    base = harness.baseline_verdict(case.raw, expected=case.expected_fields)
    strict = harness.strict_verdict(case.raw, schema=case.schema_key)
    assert base.accepted is False and base.error_code == "invalid_structured_output"
    assert strict.accepted is False


def test_v3_missing_field_not_fabricated(harness):
    case = next(
        c for c in harness.CORPUS if c.case_id == "missing_required_field"
    )
    base = harness.baseline_verdict(case.raw, expected=case.expected_fields)
    strict = harness.strict_verdict(case.raw, schema=case.schema_key)
    assert base.accepted is False
    assert strict.accepted is False


def test_v4_wrong_type_strict_catches_baseline_defers(harness):
    """Baseline presence-checks only — a wrong-typed field passes
    schema level and is rejected later by the semantic stage gate.
    The strict arm must catch it AT validation time (the DELTA this
    experiment measures) without changing the final outcome class."""
    case = next(c for c in harness.CORPUS if c.case_id == "wrong_field_type")
    base = harness.baseline_verdict(case.raw, expected=case.expected_fields)
    strict = harness.strict_verdict(case.raw, schema=case.schema_key)
    assert strict.accepted is False, "strict pydantic must reject bad types"
    # Baseline defers — record it, do not 'fix' the baseline.
    assert base.accepted is True or base.error_code is not None


def test_v5_invalid_enum_fails_closed(harness):
    case = next(c for c in harness.CORPUS if c.case_id == "invalid_enum")
    strict = harness.strict_verdict(case.raw, schema=case.schema_key)
    assert strict.accepted is False, "unknown enum/decision must fail closed"


def test_v6_unknown_capability_stays_unauthorized(harness):
    """A structurally valid proposal naming a nonexistent capability
    is a semantic/authorization rejection — NOT a JSON-format
    problem. Both arms must pass schema level and leave authority to
    the existing downstream gate."""
    case = next(
        c
        for c in harness.CORPUS
        if c.case_id == "semantically_invalid_capability"
    )
    base = harness.baseline_verdict(case.raw, expected=case.expected_fields)
    strict = harness.strict_verdict(case.raw, schema=case.schema_key)
    # Schema-level acceptance is the honest contract: the downstream
    # governed gate is what rejects the unknown capability.
    assert base.accepted is True
    assert strict.accepted is True
    assert strict.semantic_authority is False


def test_v7_extra_properties_baseline_strip_parity(harness):
    """Baseline strips surplus keys to the declared contract. The
    strict arm must not turn an otherwise-valid proposal into a
    rejection purely for a benign extra key — parity on outcome."""
    case = next(
        c
        for c in harness.CORPUS
        if c.case_id == "extra_unexpected_properties"
    )
    base = harness.baseline_verdict(case.raw, expected=case.expected_fields)
    strict = harness.strict_verdict(case.raw, schema=case.schema_key)
    assert base.accepted is True
    assert strict.accepted is True
    assert "hack" not in strict.projected


def test_v16_non_object_rejected(harness):
    case = next(c for c in harness.CORPUS if c.case_id == "non_object_output")
    base = harness.baseline_verdict(case.raw, expected=case.expected_fields)
    strict = harness.strict_verdict(case.raw, schema=case.schema_key)
    assert base.accepted is False
    assert strict.accepted is False


def test_applicable_false_passthrough(harness):
    """CONV recovery contract: applicable=false is a legitimate
    proposal, not an invalid output. Both arms must accept it."""
    case = next(
        c
        for c in harness.CORPUS
        if c.case_id == "applicable_false_passthrough"
    )
    base = harness.baseline_verdict(case.raw, expected=case.expected_fields)
    strict = harness.strict_verdict(case.raw, schema=case.schema_key)
    assert base.accepted is True
    assert strict.accepted is True


def test_fenced_json_recovery_parity(harness):
    """Baseline tolerates ```json fences. If the strict arm diverges
    here it is a false-reject, not an improvement."""
    case = next(c for c in harness.CORPUS if c.case_id == "fenced_json")
    base = harness.baseline_verdict(case.raw, expected=case.expected_fields)
    strict = harness.strict_verdict(case.raw, schema=case.schema_key)
    assert base.accepted is True
    assert strict.accepted is True, (
        "fenced output is a tolerated baseline behavior — rejecting it "
        "is a false reject on identical inputs"
    )


def test_v7b_forged_token_stays_semantic(harness):
    case = next(
        c for c in harness.CORPUS if c.case_id == "forged_candidate_token"
    )
    strict = harness.strict_verdict(case.raw, schema=case.schema_key)
    # A forged token is not a schema property — the strict arm must
    # not pretend to validate it.
    assert strict.semantic_authority is False


# ---------- V8–V12: provider/retry/budget/tool invariants ----------


def test_v11_pydanticai_retries_disabled(harness):
    """No framework-managed retry may circumvent the governed
    DELIA_LLM_CALL_MAX_ATTEMPTS budget."""
    assert harness.PYDANTICAI_RETRIES == 0


def test_v12_no_tool_execution(harness):
    """The experimental arm must not register function tools — the
    baseline rejects provider tool fields, so a tool-based output
    mode would violate the existing contract by construction."""
    assert harness.USES_FUNCTION_TOOLS is False


def test_v14_architecture_isolation():
    """pydantic_ai must not appear under app/ — the SDK is confined
    to the scripts/ evaluation boundary."""
    offenders = []
    for py in (REPO / "app").rglob("*.py"):
        text = py.read_text(encoding="utf-8")
        if re.search(r"\bpydantic_ai\b", text):
            offenders.append(str(py.relative_to(REPO)))
    assert offenders == [], f"pydantic_ai leaked into app/: {offenders}"


def test_v13_no_provider_branching_in_harness(harness):
    src = HARNESS_PATH.read_text(encoding="utf-8")
    # The harness targets the provider-neutral endpoint config; no
    # per-provider if-ladders are allowed in the experiment itself.
    assert "openrouter" not in src.lower()
    assert "kimi" not in src.lower()


def test_v18_baseline_untouched(harness):
    """The experiment must not modify the production baseline path —
    baseline_verdict is required to call the REAL InvokeModel path
    (fake TEST_ONLY port), not a re-implementation."""
    src = HARNESS_PATH.read_text(encoding="utf-8")
    assert "InvokeModel" in src, (
        "baseline arm must exercise the real InvokeModel use case"
    )


# ---------- V10: per-request counting ----------


def test_v10_live_result_counts_requests(harness):
    row = harness.LiveResult.__dataclass_fields__
    for field in (
        "provider_requests",
        "input_tokens",
        "output_tokens",
        "latency_ms",
        "invalid_output",
    ):
        assert field in row, f"LiveResult missing {field}"


# ---------- harness sanity ----------


def test_harness_exposes_verdict_shape(harness):
    fields = harness.Verdict.__dataclass_fields__
    for f in ("accepted", "projected", "error_code", "semantic_authority"):
        assert f in fields, f"Verdict missing {f}"


def test_strict_schemas_are_declared(harness):
    for key in ("capability_selection", "native_assessment"):
        assert key in harness.SCHEMAS, f"SCHEMAS missing {key}"
