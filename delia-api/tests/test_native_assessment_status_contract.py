"""Task 09 (DELIA-C3-NATIVE-ASSESSMENT-STATUS-FAIL-CLOSED-REMEDIATION-01):
the native_assessment status contract must fail CLOSED.

Task 08 (doc 201) proved the fail-open defect: any ``status`` value
outside the canonical vocabulary — including absent, null, wrong type
or empty — was coerced to ``"sufficient"`` inside
``_assess_native_path``. An invalid model decision was therefore
recorded and consumed as affirmative evidence sufficiency.

Contract under test (derived from the instruction vocabulary, not from
this file): the ONLY authorized statuses are ``sufficient``,
``foreign_evidence_required``, ``corroboration_requested`` and
``inconclusive``. Everything else is an invalid contract value and must
resolve to ``inconclusive`` — an undetermined assessment — never to
affirmative sufficiency. Both engines share ``_assess_native_path``
(LangGraph B1 calls ``gates._governed_owner_path``), so the unit-level
contract and the turn-level conformance cover A and B1 alike.
"""

from __future__ import annotations

import logging

import pytest

from app.application.capability_provision.orchestration import (
    NATIVE_ASSESSMENT_INSTRUCTION_ID,
)
from tests.test_governed_attempt_contract import build_engine
from tests.test_goal_evidence_relevance import (
    ARGUMENTS_INSTRUCTION_ID,
    CAPABILITY_SELECTION_INSTRUCTION_ID,
    GROUP_SELECTION_INSTRUCTION_ID,
    FakeProposalModel,
    FakeProvider,
    _cri_clause,
    _doc_cap,
    _doc_outcome,
    _group,
    _outcome,
    _query_cap,
)

@pytest.fixture
def capture_assessment_logs(caplog):
    """The ``app`` logger may carry a non-propagating or raised-level
    state left by earlier suites — bind it like other suites do."""
    app_logger = logging.getLogger("app")
    previous = (app_logger.propagate, app_logger.level)
    app_logger.propagate = True
    app_logger.setLevel(logging.INFO)
    try:
        with caplog.at_level(logging.INFO):
            yield caplog
    finally:
        app_logger.propagate, app_logger.level = previous


_VALID = (
    "sufficient",
    "foreign_evidence_required",
    "corroboration_requested",
    "inconclusive",
)

_INVALID = (
    "unknown_status",
    "SUFFICIENT_BUT_NOT_DEFINED",
    "SUFFICIENT",
    "suffcient",
    "insufficient",
    "",
    "  ",
    123,
    0,
    True,
    False,
    1.5,
    [],
    ["sufficient"],
    {},
    {"status": "sufficient"},
)


def _orchestrator(proposal):
    provider = FakeProvider(
        "pa",
        [_group("pa", "alpha", [_query_cap()])],
        outcomes={("alpha", "search_items"): _outcome("ok")},
    )
    clause = _cri_clause()
    orchestrator = build_engine(
        "delia",
        providers=[provider],
        model=FakeProposalModel(proposal),
        response_intelligence_enabled=True,
        cri_instruction_clause=clause.text,
        cri_instruction_version=clause.version,
    )
    return orchestrator, provider


def _assess(orchestrator):
    group = _group("pa", "alpha", [_query_cap()])
    return orchestrator._assess_native_path(
        "Qual e a descricao do produto 10080092?",
        group,
        group.capabilities[0],
        "corr-test",
        None,
        (),
        goal=None,
        deadline=None,
    )


# ---------------- R1–R3: valid vocabulary parity ----------------


@pytest.mark.parametrize("status", _VALID)
def test_r1_r2_r3_valid_statuses_preserved(status):
    orchestrator, _ = _orchestrator([{"status": status}])
    assert _assess(orchestrator) == status


# ---------------- R4–R8: invalid values fail closed ----------------


@pytest.mark.parametrize("status", _INVALID)
def test_r4_r6_r7_r8_invalid_status_never_sufficient(status):
    orchestrator, _ = _orchestrator([{"status": status}])
    result = _assess(orchestrator)
    assert result == "inconclusive"
    assert result != "sufficient"


def test_r5_missing_status_fails_closed():
    """Absent status → _propose rejects (expected_fields) → the
    undetermined outcome, never sufficiency."""
    orchestrator, _ = _orchestrator([{"limitations": []}])
    assert _assess(orchestrator) == "inconclusive"


def test_r5b_unparseable_proposal_fails_closed():
    """Non-Mapping / exhausted output → inconclusive, not sufficient."""
    orchestrator, _ = _orchestrator([["not", "a", "mapping"]])
    assert _assess(orchestrator) == "inconclusive"


def test_r15_invalid_is_not_a_positive_decision():
    """Every invalid value collapses to the same undetermined outcome —
    no silent fallback to ANY positive/vocabulary-distinct verdict."""
    orchestrator, _ = _orchestrator([{"status": "trusted_verdict"}])
    assert _assess(orchestrator) == "inconclusive"


# ---------------- R11/R12: no new model work on invalid input ----------------


def test_r11_invalid_status_consumes_no_extra_calls():
    """The invalid-value rejection is deterministic — it spends no
    model call, so the invocation budget and TurnDeadline are
    untouched (one assessment request only)."""
    model = FakeProposalModel([{"status": "bogus"}])
    provider = FakeProvider(
        "pa",
        [_group("pa", "alpha", [_query_cap()])],
        outcomes={("alpha", "search_items"): _outcome("ok")},
    )
    clause = _cri_clause()
    orchestrator = build_engine(
        "delia",
        providers=[provider],
        model=model,
        llm_call_max_attempts=3,
        response_intelligence_enabled=True,
        cri_instruction_clause=clause.text,
        cri_instruction_version=clause.version,
    )
    assert _assess(orchestrator) == "inconclusive"
    assessment_calls = [
        r
        for r in model.requests
        if r.task_purpose_id == NATIVE_ASSESSMENT_INSTRUCTION_ID
    ]
    assert len(assessment_calls) == 1


# ---------------- turn-level conformance (R9/R10/R13/R14/R16) ----------------


def _two_provider_turn(status, engine):
    """Two-group turn whose assessment stage returns ``status``.

    Queue mirrors _reuse_proposal ordering (generic items feed unrouted
    stages in order): turn_goal, native_assessment, then the owner
    arguments proposal.
    """
    pa = FakeProvider(
        "pa",
        [_group("pa", "alpha", [_query_cap()])],
        outcomes={
            ("alpha", "search_items"): _outcome(
                "ok",
                structured={"items": [{"name": "TERM. BALA"}]},
            )
        },
    )
    pb = FakeProvider(
        "pb",
        [_group("pb", "beta", [_doc_cap()])],
        outcomes={("beta", "read_guidance"): _doc_outcome()},
    )
    proposal = [
        {
            GROUP_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "capability_group_id": "pa:alpha",
            },
            CAPABILITY_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "remote_name": "search_items",
            },
            ARGUMENTS_INSTRUCTION_ID: {"arguments": {"query": "x"}},
        },
        {"goal_class": "record_lookup"},
        {"status": status}
        if status != "__absent__"
        else {"limitations": []},
        {ARGUMENTS_INSTRUCTION_ID: {"arguments": {"query": "bala"}}},
    ]
    clause = _cri_clause()
    model = FakeProposalModel(proposal)
    attempt_engine = build_engine(
        engine,
        providers=[pa, pb],
        model=model,
        response_intelligence_enabled=True,
        cri_instruction_clause=clause.text,
        cri_instruction_version=clause.version,
    )
    attempt = attempt_engine.attempt(
        "Me de dois exemplos de terminal bala"
    )
    return attempt, pa, pb, model


def _assessment_decisions(caplog):
    return [
        r.getMessage()
        for r in caplog.records
        if "stage=native_assessment" in r.getMessage()
        and "decision=" in r.getMessage()
    ]


@pytest.mark.parametrize("engine", ["delia", "langgraph_b0", "langgraph"])
def test_r9_r10_r13_r14_invalid_status_turn_stays_governed(
    engine, capture_assessment_logs
):
    """Invalid status → the recorded/logged decision is inconclusive
    (never sufficient); the turn still follows the governed native
    path — the invalid decision neither authorizes nor fabricates
    anything."""
    attempt, pa, pb, model = _two_provider_turn(
        "not_a_real_status", engine
    )
    decisions = _assessment_decisions(capture_assessment_logs)
    assert any("decision=invalid_status_rejected" in m for m in decisions)
    assert any("decision=inconclusive" in m for m in decisions)
    assert not any("decision=sufficient" in m for m in decisions)
    # Native path: target owner ran; the invalid decision triggered no
    # foreign (beta) invocation.
    assert pa.calls
    assert not pb.calls
    # The outcome is a typed governed attempt — never a fabricated
    # business result.
    assert attempt is not None


@pytest.mark.parametrize("engine", ["delia", "langgraph_b0", "langgraph"])
def test_r18_valid_statuses_turn_parity(
    engine, capture_assessment_logs
):
    attempt, pa, pb, model = _two_provider_turn("sufficient", engine)
    decisions = _assessment_decisions(capture_assessment_logs)
    assert any("decision=sufficient" in m for m in decisions)
    assert not any(
        "decision=invalid_status_rejected" in m for m in decisions
    )
    assert pa.calls


@pytest.mark.parametrize("engine", ["delia", "langgraph_b0", "langgraph"])
def test_r18b_missing_status_turn_fails_closed(
    engine, capture_assessment_logs
):
    attempt, pa, pb, model = _two_provider_turn("__absent__", engine)
    decisions = _assessment_decisions(capture_assessment_logs)
    assert any("decision=inconclusive" in m for m in decisions)
    assert not any("decision=sufficient" in m for m in decisions)


# ---------------- R17: PREPARE/ACT untouched ----------------


def test_r17_invalid_status_cannot_authorize_material_action():
    """An invalid assessment contributes no authorization: the native
    default is unchanged — no foreign fan-out, no extra capability,
    and PREPARE/ACT gates downstream remain the sole material-action
    authority."""
    orchestrator, _ = _orchestrator([{"status": "act_now"}])
    assert _assess(orchestrator) == "inconclusive"
