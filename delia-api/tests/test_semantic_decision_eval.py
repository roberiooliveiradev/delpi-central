"""Task 10 (DELIA-C3-SEMANTIC-INTELLIGENCE-PLUGGABLE-AB-01): stage-level
semantic decision eval — experiment-harness invariants.

The harness lives under ``delia-api/scripts/`` (isolated evaluation
boundary, same pattern as the Task 08 harness). These tests pin the
corpus semantics, the reuse of the REAL stage contracts (instruction
text, block builders, downstream validators), and the architectural
constraints: no dspy import under ``app/``, no framework tool
execution, no provider-name branching, no production-code change.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
HARNESS_PATH = REPO / "scripts" / "semantic_decision_eval.py"


def _load_harness():
    spec = importlib.util.spec_from_file_location(
        "semantic_decision_eval", HARNESS_PATH
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def harness():
    return _load_harness()


# ---------- corpus coverage ----------

_CASE_CLASSES = {"REAL_INCIDENT", "HISTORICAL_REPLAY",
                 "DETERMINISTIC_FIXTURE", "SYNTHETIC_STRESS", "HELD_OUT"}


def test_corpus_classes_are_declared(harness):
    for case in (*harness.CAPABILITY_CASES, *harness.GROUP_CASES):
        assert case.klass in _CASE_CLASSES, case.case_id
    for case in harness.RELEVANCE_CASES:
        assert case.klass in _CASE_CLASSES, case.case_id


def test_real_incidents_replayed(harness):
    """Docs 188/202 incidents must be present — product by code and
    terminal-bala examples exist in both selection and relevance
    corpora."""
    cap_ids = {c.case_id for c in harness.CAPABILITY_CASES}
    rel_ids = {c.case_id for c in harness.RELEVANCE_CASES}
    real_caps = {
        c.case_id for c in harness.CAPABILITY_CASES
        if c.klass == "REAL_INCIDENT"
    }
    assert "cap_product_by_code" in real_caps
    assert "cap_terminal_bala_examples" in real_caps
    assert "rel_corresponding" in rel_ids
    assert "rel_wrong_subject_balanca" in rel_ids


def test_paraphrase_and_rename_coverage(harness):
    ids = {c.case_id for c in harness.CAPABILITY_CASES}
    assert any("paraphrase" in i for i in ids)
    assert any(c.renamed for c in harness.CAPABILITY_CASES)
    assert any(c.renamed for c in harness.GROUP_CASES)
    # unknown handling: at least one not-applicable expectation.
    assert any(c.expect_not_applicable for c in harness.CAPABILITY_CASES)
    assert any(c.expect_not_applicable for c in harness.GROUP_CASES)


def test_held_out_cases_exist(harness):
    assert any(
        c.klass == "HELD_OUT" for c in harness.CAPABILITY_CASES
    )
    assert any(
        c.klass == "HELD_OUT" for c in harness.RELEVANCE_CASES
    )


def test_every_positive_case_has_expected_surface(harness):
    for case in (*harness.CAPABILITY_CASES, *harness.GROUP_CASES):
        if not case.expect_not_applicable:
            assert case.expected, case.case_id


# ---------- real-contract reuse ----------

def test_harness_uses_real_instruction_text(harness):
    """Baseline arm must carry the governed v25 instruction — not a
    paraphrased eval prompt."""
    instr = harness._instruction(
        "delia.capability_orchestration.select_capability"
    )
    assert "applicable" in instr and "remote_name" in instr
    assert len(instr) > 1000


def test_harness_uses_real_validators(harness):
    src = HARNESS_PATH.read_text(encoding="utf-8")
    assert "_capability_from_selection_proposal" in src
    assert "_resolve_live_group_key" in src
    assert "parse_goal_evidence_judgment" in src
    assert "_capability_payload" in src
    assert "_group_summaries" in src


def test_downstream_gate_rejects_unknown_remote_name(harness):
    """S6/S10: an invented capability stays unauthorized — the same
    deterministic gate used by production."""
    group = harness.davi_group()
    proposal = {"applicable": True, "remote_name": "nope_not_listed"}
    status, cap = harness._capability_from_selection_proposal(
        proposal, list(group.capabilities)
    )
    assert status == "inconclusive"
    assert cap is None


def test_downstream_gate_rejects_forged_group(harness):
    groups = harness.all_groups()
    assert (
        harness._resolve_live_group_key("mcp:evil", groups) is None
    )


def test_catalog_fixture_has_davi_surface(harness):
    group = harness.davi_group()
    names = {c.remote_name for c in group.capabilities}
    assert "search_products" in names
    assert "discover_delpi_information" in names
    # every fixture capability is invocable-in-phase typed
    for cap in group.capabilities:
        assert cap.operation_class.value in (
            "DISCOVERY", "READ", "ANALYSIS", "PREPARE", "ACT"
        )


# ---------- eval-boundary isolation ----------

def test_no_dspy_under_app():
    offenders = []
    for py in (REPO / "app").rglob("*.py"):
        if re.search(r"\bdspy\b", py.read_text(encoding="utf-8")):
            offenders.append(str(py.relative_to(REPO)))
    assert offenders == [], f"dspy leaked into app/: {offenders}"


def test_no_dspy_at_module_level_in_harness(harness):
    """dspy may only be imported inside function bodies — the module
    must import cleanly without the SDK installed."""
    top = HARNESS_PATH.read_text(encoding="utf-8")
    head = top.split("def _dspy_lm")[0]
    assert "import dspy" not in head


def test_no_provider_branching_in_harness():
    src = HARNESS_PATH.read_text(encoding="utf-8").lower()
    assert "openrouter" not in src
    assert "kimi" not in src


def test_eval_model_is_local(harness):
    assert harness.EVAL_MODEL.startswith("delia-json")
    assert "localhost" in harness.OLLAMA_BASE_URL


def test_result_shape_counts_requests(harness):
    fields = harness.StageResult.__dataclass_fields__
    for f in (
        "arm",
        "status",
        "invalid_output",
        "input_tokens",
        "output_tokens",
        "latency_ms",
    ):
        assert f in fields, f"StageResult missing {f}"


def test_baseline_arm_untouched_contract(harness):
    """The baseline request must wrap input in <user_message> and the
    tagged block — the exact _model_stage_proposal shape."""
    req = harness._request(
        "texto",
        "capabilities",
        "{}",
        "instr",
        "delia.capability_orchestration.select_capability",
        ("applicable",),
    )
    assert req.input_text.startswith("<user_message>\ntexto")
    assert "<capabilities>\n{}\n</capabilities>" in req.input_text
    assert req.instruction_content == "instr"


def test_no_production_requirements_change():
    reqs = (REPO / "requirements.txt").read_text(encoding="utf-8")
    assert "dspy" not in reqs.lower()
