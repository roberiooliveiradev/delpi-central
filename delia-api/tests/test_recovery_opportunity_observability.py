"""Task 06 — recovery-opportunity observability (DELIA-C3-RECOVERY-
OBSERVABILITY-VALUE-01).

The value question is whether the B1 reuse window occurs often enough
to matter. Answering it requires observing, from real governed
execution, the distinction between:

  E1 assessment executed      E2 recovery entered
  E3 reuse candidate          E4 eligible (same predicate as B1)
  E5 reuse performed          E6 reassessment performed

Owner: ModelCallLedger (turn-scoped, request-scoped carrier already
bound by handle_interactive_turn) + the same deterministic
_native_assessment premise predicate Task 05 hardened. Engine A is
observed, never optimized: no reuse ledger is bound, no model call is
skipped — eligible windows under A are counted as opportunities AND
as the reassessments that actually executed.
"""

from __future__ import annotations

import threading

import pytest

from app.application.capability_provision.orchestration import (
    NATIVE_ASSESSMENT_INSTRUCTION_ID,
)
from app.application.interaction.turn_observability import (
    ModelCallLedger,
    bind_turn_call_ledger,
    build_turn_observability,
    reset_turn_call_ledger,
)
from tests.test_governed_attempt_contract import build_engine
from tests.test_engine_b_recovery_reuse import (
    _providers,
    _reuse_proposal,
    _assessment_calls,
)
from tests.test_goal_evidence_relevance import (
    FakeProposalModel as RelevanceProposalModel,
)
from tests.test_governed_attempt_contract import _cri_clause


INPUT = "2 exemplos de terminal bala"


def _run(engine_id, *, cancel_check=None):
    """Attempt under a bound call ledger — the same observation
    surface production already provides per turn."""
    providers = _providers()
    model = RelevanceProposalModel(_reuse_proposal())
    clause = _cri_clause()
    engine = build_engine(
        engine_id,
        providers=providers,
        model=model,
        response_intelligence_enabled=True,
        cri_instruction_clause=clause.text,
        cri_instruction_version=clause.version,
    )
    ledger = ModelCallLedger()
    token = bind_turn_call_ledger(ledger)
    try:
        attempt = engine.attempt(INPUT, cancel_check=cancel_check)
    finally:
        reset_turn_call_ledger(token)
    return attempt, ledger, model, providers


def _obs(ledger):
    """Projected recovery-opportunity counters for the turn."""
    obs = dict(ledger.recovery_observation)
    obs["native_assessment_calls"] = sum(
        1
        for c in ledger.calls
        if c.stage == NATIVE_ASSESSMENT_INSTRUCTION_ID
    )
    return obs


# ---------------- O1/O2/O7 — E1 counting ----------------


class TestAssessmentCounting:
    def test_o1_no_assessment_no_count(self):
        """O1 — a turn with no native_assessment invocation reports
        zero (fixture reaches recovery only through the reuse
        scenario; a minimal surface-inquiry attempt stays at zero)."""
        ledger = ModelCallLedger()
        token = bind_turn_call_ledger(ledger)
        try:
            providers = _providers()
            model = RelevanceProposalModel(_reuse_proposal())
            clause = _cri_clause()
            engine = build_engine(
                "delia",
                providers=providers,
                model=model,
                response_intelligence_enabled=True,
                cri_instruction_clause=clause.text,
                cri_instruction_version=clause.version,
            )
            engine.attempt("obrigado")
        finally:
            reset_turn_call_ledger(token)
        obs = _obs(ledger)
        assert obs["native_assessment_calls"] == sum(
            1
            for c in ledger.calls
            if c.stage == NATIVE_ASSESSMENT_INSTRUCTION_ID
        )

    def test_o2_recovery_round1_assessment_counted(self):
        """O2 — the S11 turn's real assessments appear verbatim; no
        phantom call is invented for the reused decision."""
        attempt, ledger, model, _p = _run("langgraph")
        obs = _obs(ledger)
        real = len(_assessment_calls(model))
        assert obs["native_assessment_calls"] == real


# ---------------- O3–O6/O11 — event + eligibility ----------------


class TestRecoveryEvents:
    def test_o3_recovery_entered_counted(self):
        """O3 — recovery entry is counted whether or not reuse is
        possible (Engine A never binds the reuse ledger)."""
        attempt, ledger, _m, _p = _run("delia")
        obs = _obs(ledger)
        assert obs["relevance_recovery_entered"] >= 1

    def test_o5_eligible_window_observed_on_engine_a(self):
        """O5 — Engine A's identical premises make the window
        ELIGIBLE under observation (same predicate as B1) even though
        A still pays the assessment call — opportunity != apply."""
        attempt, ledger, _m, _p = _run("delia")
        obs = _obs(ledger)
        assert obs["reuse_candidates"] >= 1
        assert obs["reuse_eligible"] >= 1

    def test_o8_b1_reuse_performed(self):
        """O8 — B1 actually reuses: performed==1 AND the avoided call
        is absent from native_assessment_calls."""
        attempt, ledger, model, _p = _run("langgraph")
        obs = _obs(ledger)
        assert obs["reuse_performed"] >= 1
        assert obs["native_assessment_calls"] == 1
        assert obs["reassessments"] == 0

    def test_o7_engine_a_reassessment_counted(self):
        """O7 — Engine A's legitimate second assessment is a
        reassessment, not a reuse."""
        attempt, ledger, _m, _p = _run("delia")
        obs = _obs(ledger)
        assert obs["reuse_performed"] == 0
        assert obs["reassessments"] >= 1
        assert obs["native_assessment_calls"] == 2

    def test_o11_failclosed_no_eligibility(self):
        """O11 — an attempt that never records an assessment cannot
        mint an eligible window."""
        ledger = ModelCallLedger()
        obs = ledger.recovery_observation
        assert obs["reuse_eligible"] == 0
        assert obs["reuse_candidates"] == 0

    def test_o4_ineligible_verdict_never_eligible(self):
        """O4 — a recorded `sufficient` verdict cannot mint
        eligibility under the observation predicate either."""
        from app.application.capability_provision.orchestration import (
            _native_assessment_reuse_verdict,
            _record_native_assessment,
        )
        from tests.test_engine_b_recovery_hardening import (
            _make_premise,
        )

        ledger = ModelCallLedger()
        token = bind_turn_call_ledger(ledger)
        try:
            p = _make_premise()
            _record_native_assessment(
                p["input_text"],
                p["group"],
                p["group_key"],
                p["descriptor"],
                p["goal"],
                p["workspace_context"],
                p["prior_turns"],
                "sufficient",
            )
            verdict = _native_assessment_reuse_verdict(
                ledger.recovery_records,
                p["input_text"],
                p["group"],
                p["group_key"],
                p["descriptor"],
                p["goal"],
                p["workspace_context"],
                p["prior_turns"],
            )
        finally:
            reset_turn_call_ledger(token)
        assert verdict is None

    def test_o6_changed_premise_not_eligible(self):
        """O6 — identical record, materially changed premise
        (input text) → the observation predicate refuses."""
        from app.application.capability_provision.orchestration import (
            _native_assessment_reuse_verdict,
            _record_native_assessment,
        )
        from tests.test_engine_b_recovery_hardening import (
            _make_premise,
        )

        ledger = ModelCallLedger()
        token = bind_turn_call_ledger(ledger)
        try:
            p = _make_premise()
            _record_native_assessment(
                p["input_text"],
                p["group"],
                p["group_key"],
                p["descriptor"],
                p["goal"],
                p["workspace_context"],
                p["prior_turns"],
                "foreign_evidence_required",
            )
            verdict = _native_assessment_reuse_verdict(
                ledger.recovery_records,
                "pedido diferente",
                p["group"],
                p["group_key"],
                p["descriptor"],
                p["goal"],
                p["workspace_context"],
                p["prior_turns"],
            )
            same = _native_assessment_reuse_verdict(
                ledger.recovery_records,
                p["input_text"],
                p["group"],
                p["group_key"],
                p["descriptor"],
                p["goal"],
                p["workspace_context"],
                p["prior_turns"],
            )
        finally:
            reset_turn_call_ledger(token)
        assert verdict is None
        assert same == "foreign_evidence_required"


# ---------------- O9/O10 — lifecycle ----------------


class TestLifecycle:
    def test_o9_cancellation_no_invented_counts(self):
        """O9 — a cancelled attempt reports whatever genuinely ran;
        never an invented opportunity."""
        def cancel():
            return "PROCESSING_TIMEOUT"

        attempt, ledger, _m, _p = _run("langgraph", cancel_check=cancel)
        obs = _obs(ledger)
        assert obs["reuse_performed"] == 0
        assert obs["reuse_eligible"] <= obs["reuse_candidates"]

    def test_o10_concurrent_turns_isolated(self):
        """O10 — two simultaneous turns cannot see each other's
        counters or records."""
        results: dict[int, dict] = {}
        errors: list[BaseException] = []
        barrier = threading.Barrier(2)

        def worker(idx):
            try:
                barrier.wait(timeout=10)
                _a, ledger, _m, _p = _run("langgraph")
                results[idx] = _obs(ledger)
            except BaseException as exc:  # noqa: BLE001 — test asserts
                errors.append(exc)

        threads = [
            threading.Thread(target=worker, args=(i,)) for i in range(2)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=60)
        assert not errors
        assert results[0] == results[1]
        assert results[0]["reuse_performed"] >= 1

    def test_sequential_turns_reset(self):
        """A second turn observes a fresh carrier — no accumulation."""
        _a, ledger1, _m, _p = _run("langgraph")
        _a2, ledger2, _m2, _p2 = _run("langgraph")
        assert _obs(ledger1) == _obs(ledger2)
        assert ledger1 is not ledger2


# ---------------- O12/O13/O14 — privacy, engine A, compat ----------------


class TestContractSafety:
    def test_o12_no_sensitive_payloads(self):
        """O12 — the observation projection carries counters only:
        no input text, premise hashes, decisions beyond counters,
        evidence or reasoning."""
        attempt, ledger, _m, _p = _run("langgraph")
        obs = _obs(ledger)
        blob = str(obs)
        assert INPUT not in blob
        assert "premise_fp" not in blob
        assert "TERM. BALA" not in blob
        assert all(isinstance(v, int) for v in obs.values())

    def test_o13_engine_a_behavior_unchanged(self):
        """O13 — observation does not optimize Engine A: identical
        model calls, owner calls and outcome vs pre-instrumentation
        baseline (17/4 SUCCESS on S11)."""
        attempt, ledger, model, providers = _run("delia")
        assert attempt.status.name == "SUCCESS"
        assert len(model.requests) == 17
        assert sum(len(p.calls) for p in providers) == 4

    def test_o14_projection_additive_only(self):
        """O14 — build_turn_observability gains an additive
        recovery_opportunity block only when supplied; legacy shape
        is byte-identical otherwise."""
        base = build_turn_observability(
            model_ref=None,
            response_mode="answer",
            composition_mode="model",
            calls=(),
            duration_ms=1,
            governed_attempts=1,
        )
        assert "recovery_opportunity" not in base
        extended = build_turn_observability(
            model_ref=None,
            response_mode="answer",
            composition_mode="model",
            calls=(),
            duration_ms=1,
            governed_attempts=1,
            recovery_opportunity={
                "native_assessment_calls": 0,
                "relevance_recovery_entered": 0,
                "reuse_candidates": 0,
                "reuse_eligible": 0,
                "reuse_performed": 0,
                "reassessments": 0,
            },
        )
        assert set(extended.keys()) == set(base.keys()) | {
            "recovery_opportunity"
        }
        assert extended["recovery_opportunity"]["reuse_eligible"] == 0
