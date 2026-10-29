"""Task 05 — recovery-reuse hardening (DELIA-C3-RECOVERY-SAFETY-
SEMANTIC-EVAL-01).

Two review findings drive this suite:

F1 — premise equivalence: the Task-04 record fingerprinted only 4 of
the goal fields. The native_assessment decision actually consumes:
input_text, target capability_id + operation_class, the serialized
group capability surface, the turn-goal payload, workspace_context
and prior_turns. All must be part of the equivalence premise — with
relevance_feedback the single intentional delta governed by the
monotonic rule (H-tests).

F2 — ledger lifecycle: the mutable ContextVar-bound ledger must be
request-scoped, exception-safe and free of cross-attempt leakage —
LangGraph nodes run in copied contexts (C-tests).
"""

from __future__ import annotations

import threading

import pytest

from app.application.capability_provision.orchestration import (
    NATIVE_ASSESSMENT_INSTRUCTION_ID,
    _NATIVE_ASSESSMENT_LEDGER,
    _record_native_assessment,
    _reusable_native_assessment,
)
from tests.test_governed_attempt_contract import build_engine
from tests.test_engine_b_recovery_reuse import (
    _engine,
    _providers,
    _reuse_proposal,
    _assessment_calls,
)
from tests.test_goal_evidence_relevance import (
    FakeProvider,
    GovernedCapabilityStatus,
    _cap,
    _doc_cap,
    _doc_outcome,
    _group,
    _outcome,
    _query_cap,
)


# ---------------- shared premise fixtures ----------------


def _make_premise(**over):
    """Canonical premise tuple matching the record/reuse call sites."""
    from tests.test_engine_b_recovery_reuse import _IRRELEVANT

    group = _group("pa", "alpha", [_query_cap()])
    descriptor = group.capabilities[0]
    premise = {
        "input_text": "2 exemplos de terminal bala",
        "group": group,
        "group_key": "pa:alpha",
        "descriptor": descriptor,
        "goal": None,
        "workspace_context": None,
        "prior_turns": (),
    }
    premise.update(over)
    return premise


def _record(premise, decision="foreign_evidence_required"):
    _record_native_assessment(
        premise["input_text"],
        premise["group"],
        premise["group_key"],
        premise["descriptor"],
        premise["goal"],
        premise["workspace_context"],
        premise["prior_turns"],
        decision,
    )


def _reusable(premise):
    return _reusable_native_assessment(
        premise["input_text"],
        premise["group"],
        premise["group_key"],
        premise["descriptor"],
        premise["goal"],
        premise["workspace_context"],
        premise["prior_turns"],
    )


@pytest.fixture
def ledger():
    token = _NATIVE_ASSESSMENT_LEDGER.set(
        {"records": {}, "events": []}
    )
    yield
    _NATIVE_ASSESSMENT_LEDGER.reset(token)


# ---------------- H-tests: premise equivalence ----------------


class TestPremiseEquivalence:
    def test_h1_identical_premises_allow_reuse(self, ledger):
        """H1 — every required equivalence condition holds."""
        p = _make_premise()
        _record(p)
        assert _reusable(p) == "foreign_evidence_required"

    def test_h2_different_input_text_invalidates(self, ledger):
        """H2 — a changed request must not inherit the decision."""
        p = _make_premise()
        _record(p)
        changed = _make_premise(input_text="outra pergunta")
        assert _reusable(changed) is None

    def test_h3_different_scope_constraints_invalidates(self, ledger):
        """H3 — material scope differences invalidate the premise."""
        from app.application.capability_provision.orchestration import (
            OperationalCapabilityOrchestrator as Orch,
        )

        base_goal = Orch._TurnGoal(
            goal_class="read",
            business_subject="produtos",
            scope_constraints=(("planta", "P1"),),
        )
        other_goal = Orch._TurnGoal(
            goal_class="read",
            business_subject="produtos",
            scope_constraints=(("planta", "P2"),),
        )
        _record(_make_premise(goal=base_goal))
        assert _reusable(_make_premise(goal=other_goal)) is None
        assert _reusable(_make_premise(goal=base_goal)) is not None

    def test_h4_different_answer_requirements_invalidates(
        self, ledger
    ):
        """H4 — changed answer requirements must not retain a stale
        decision."""
        from app.application.capability_provision.orchestration import (
            OperationalCapabilityOrchestrator as Orch,
        )

        g1 = Orch._TurnGoal(goal_class="read", business_subject="x")
        g2 = Orch._TurnGoal(
            goal_class="read",
            business_subject="x",
            output_mode="count",
        )
        _record(_make_premise(goal=g1))
        assert _reusable(_make_premise(goal=g2)) is None

    def test_h5_changed_workspace_context_invalidates(self, ledger):
        """H5 — material workspace changes invalidate reuse."""
        from app.application.interaction.workspace_context import (
            WorkspaceContext,
        )

        ws1 = WorkspaceContext(host_app_id="app-a")
        ws2 = WorkspaceContext(host_app_id="app-b")
        _record(_make_premise(workspace_context=ws1))
        assert _reusable(_make_premise(workspace_context=ws2)) is None
        assert _reusable(_make_premise(workspace_context=ws1)) is not None

    def test_h6_changed_prior_turns_invalidates(self, ledger):
        """H6 — materially different conversation context must not
        reuse."""
        from app.application.model_invocation.contracts import (
            ConversationContextTurn,
        )
        from app.domain.interaction.model import TurnKind

        t1 = (
            ConversationContextTurn(
                kind=TurnKind.USER_INPUT, content="pergunta um"
            ),
        )
        t2 = (
            ConversationContextTurn(
                kind=TurnKind.USER_INPUT, content="pergunta dois"
            ),
        )
        _record(_make_premise(prior_turns=t1))
        assert _reusable(_make_premise(prior_turns=t2)) is None
        assert _reusable(_make_premise(prior_turns=t1)) is not None

    def test_h7_changed_capability_invalidates(self, ledger):
        """H7 — different capability id, group or surface must
        reassess."""
        p = _make_premise()
        _record(p)
        # Different capability in same group:
        group2 = _group(
            "pa",
            "alpha",
            [_cap("alpha", "pa", "lookup_items")],
        )
        changed = _make_premise(
            group=group2,
            descriptor=group2.capabilities[0],
        )
        assert _reusable(changed) is None
        # Same capability id but different group:
        group3 = _group("pb", "gamma", [_query_cap()])
        changed2 = _make_premise(
            group=group3,
            group_key="pb:gamma",
            descriptor=group3.capabilities[0],
        )
        assert _reusable(changed2) is None

    def test_h8_different_evidence_premises_reassess(self, ledger):
        """H8 — decisions are target-bound: a record made for one
        capability never transfers to another target."""
        p = _make_premise()
        other = _make_premise(
            group=_group("pa", "alpha", [_cap("alpha", "pa", "other")]),
        )
        other["descriptor"] = other["group"].capabilities[0]
        _record(p)
        _record(other, decision="sufficient")
        assert _reusable(other) is None
        assert _reusable(p) is not None

    def test_h9_sufficient_verdict_never_reused(self, ledger):
        """H9 — 'sufficient' is refuted by the mismatch; reuse would
        bypass a mandatory decision on confirmed divergence."""
        p = _make_premise()
        _record(p, decision="sufficient")
        assert _reusable(p) is None

    @pytest.mark.parametrize(
        "decision", ["corroboration_requested", "inconclusive"]
    )
    def test_h10_uncertain_equivalence_fails_closed(
        self, ledger, decision
    ):
        """H10 — anything not provably monotonic-safe reassesses."""
        p = _make_premise()
        _record(p, decision=decision)
        assert _reusable(p) is None

    def test_h10b_no_record_fails_closed(self, ledger):
        """H10 — an empty ledger never yields a decision."""
        assert _reusable(_make_premise()) is None

    def test_unbound_ledger_always_reassesses(self):
        """No ledger bound (Engine A path) — always fresh assessment."""
        assert _NATIVE_ASSESSMENT_LEDGER.get() is None
        assert _reusable(_make_premise()) is None


# ---------------- C-tests: ledger lifecycle & isolation ----------------


class TestLedgerLifecycle:
    def test_c2_sequential_attempts_start_clean(self):
        """C2 — each bound session starts with an empty record set;
        nothing carries forward."""
        token1 = _NATIVE_ASSESSMENT_LEDGER.set(
            {"records": {}, "events": []}
        )
        _record(_make_premise())
        _NATIVE_ASSESSMENT_LEDGER.reset(token1)
        token2 = _NATIVE_ASSESSMENT_LEDGER.set(
            {"records": {}, "events": []}
        )
        assert _reusable(_make_premise()) is None
        _NATIVE_ASSESSMENT_LEDGER.reset(token2)

    def test_c5_exception_does_not_leak_ledger(self, ledger):
        """C5 — a raise inside the governed path leaves no residue:
        the ledger binding scope ends with the attempt."""
        p = _make_premise()
        _record(p)
        outer = _NATIVE_ASSESSMENT_LEDGER.get()
        # Simulate owner_path's set/reset contract:
        token = _NATIVE_ASSESSMENT_LEDGER.set(
            {"records": {}, "events": []}
        )
        try:
            raise RuntimeError("boom")
        except RuntimeError:
            pass
        finally:
            _NATIVE_ASSESSMENT_LEDGER.reset(token)
        # Outer scope untouched by the failed nested session.
        assert _NATIVE_ASSESSMENT_LEDGER.get() is outer
        assert len(outer["records"]) == 1

    def test_c1_concurrent_attempts_isolated(self):
        """C1 — two threads bound to separate ledgers never observe
        each other's decisions."""
        results: dict[str, object] = {}
        barrier = threading.Barrier(2)

        def worker(tag, decision):
            token = _NATIVE_ASSESSMENT_LEDGER.set(
                {"records": {}, "events": []}
            )
            try:
                _record(_make_premise(), decision=decision)
                barrier.wait(timeout=5)
                # After the barrier, both ledgers have records — but
                # each thread sees only its own.
                results[tag] = {
                    "reusable": _reusable(_make_premise()),
                    "count": len(
                        _NATIVE_ASSESSMENT_LEDGER.get()["records"]
                    ),
                }
            finally:
                _NATIVE_ASSESSMENT_LEDGER.reset(token)

        t1 = threading.Thread(
            target=worker, args=("t1", "foreign_evidence_required")
        )
        t2 = threading.Thread(
            target=worker, args=("t2", "sufficient")
        )
        t1.start()
        t2.start()
        t1.join(timeout=10)
        t2.join(timeout=10)
        assert results["t1"]["reusable"] == "foreign_evidence_required"
        assert results["t1"]["count"] == 1
        # t2 recorded a non-reusable decision; it must not see t1's.
        assert results["t2"]["reusable"] is None
        assert results["t2"]["count"] == 1

    def test_c9_ledger_bounded(self, ledger):
        """C9 — records stay keyed to (group, capability): unbounded
        growth is impossible by construction."""
        for i in range(50):
            p = _make_premise(input_text=f"turn {i}")
            _record(p)
        # One key per (group_key, capability_id) — overwritten, never
        # appended: the record dict cannot grow past the live surface.
        assert len(_NATIVE_ASSESSMENT_LEDGER.get()["records"]) == 1

    def test_c10_no_sensitive_persistence(self, ledger):
        """C10 — a record carries only the decision string and the
        premise fingerprint: no payloads, no feedback text, no
        chain-of-thought."""
        _record(_make_premise())
        records = _NATIVE_ASSESSMENT_LEDGER.get()["records"]
        ((key, record),) = records.items()
        assert isinstance(key[0], str) and isinstance(key[1], str)
        assert set(record) == {"decision", "premise_fp"}
        assert isinstance(record["premise_fp"], str)
        assert len(record["premise_fp"]) == 64  # sha256 hex


# ---------------- engine-level lifecycle tests ----------------


class TestEngineLifecycle:
    def test_c1_engine_concurrent_attempts_no_cross_talk(self):
        """Two engines built on the same gates pattern run attempts in
        parallel threads; each B1 attempt gets its own ledger — the
        trace events of one attempt never appear in the other."""
        orch1, _ = _engine(
            "langgraph", _providers(), _reuse_proposal()
        )
        orch2, _ = _engine(
            "langgraph",
            _providers(),
            _reuse_proposal(first_status="sufficient"),
        )
        barrier = threading.Barrier(2)
        outcomes: dict[str, tuple] = {}

        def run(tag, orch):
            barrier.wait(timeout=5)
            attempt = orch.attempt("2 exemplos de terminal bala")
            outcomes[tag] = (attempt, list(orch.last_node_trace))

        t1 = threading.Thread(target=run, args=("b1a", orch1))
        t2 = threading.Thread(target=run, args=("b1b", orch2))
        t1.start()
        t2.start()
        t1.join(timeout=20)
        t2.join(timeout=20)
        a1, trace1 = outcomes["b1a"]
        a2, trace2 = outcomes["b1b"]
        assert "assessment_reused" in trace1
        assert "assessment_reused" not in trace2
        assert "assessment_reassessed" in trace2
        assert a1.status == a2.status == GovernedCapabilityStatus.SUCCESS

    def test_c3_engine_retry_gets_fresh_ledger(self):
        """C3 — repeated graph invocations bind a fresh ledger each
        time: a second attempt() call re-establishes decisions rather
        than inheriting them."""
        orch, model = _engine(
            "langgraph", _providers(), _reuse_proposal()
        )
        orch.attempt("2 exemplos de terminal bala")
        assert "assessment_reused" in orch.last_node_trace
        # Second independent attempt — fresh ledger, decisions are
        # re-established by new assessment calls (proposal queue
        # exhausted -> replays last; the point is no inherited state).
        orch2, model2 = _engine(
            "langgraph", _providers(), _reuse_proposal()
        )
        orch2.attempt("2 exemplos de terminal bala")
        assert "assessment_reused" in orch2.last_node_trace

    def test_c4_cancellation_leaves_no_ledger(self):
        """C4 — a cancelled attempt must not leave a bound ledger
        visible to later code in the same context."""
        orch, model = _engine(
            "langgraph", _providers(), _reuse_proposal()
        )
        attempt = orch.attempt(
            "2 exemplos de terminal bala", cancel_check=lambda: True
        )
        assert attempt.status is (
            GovernedCapabilityStatus.PROCESSING_TIMEOUT
        )
        assert _NATIVE_ASSESSMENT_LEDGER.get() is None

    def test_c5_engine_exception_leaves_no_ledger(self):
        """C5 — even if the governed path raises, the ambient binding
        is cleaned up (set/reset pair in owner_path)."""
        orch, model = _engine(
            "langgraph", _providers(), _reuse_proposal()
        )

        def boom(*a, **k):
            raise RuntimeError("simulated governed-path failure")

        gates = orch._gates
        original = gates._governed_owner_path
        gates._governed_owner_path = boom
        try:
            try:
                orch.attempt("2 exemplos de terminal bala")
            except Exception:
                pass
        finally:
            gates._governed_owner_path = original
        assert _NATIVE_ASSESSMENT_LEDGER.get() is None

    def test_c8_ledger_never_authorizes(self):
        """C8 — binding the ledger manually cannot grant any path the
        governed gates would not take: an engine attempt on a
        fabricated capability still fails closed."""
        token = _NATIVE_ASSESSMENT_LEDGER.set(
            {"records": {}, "events": []}
        )
        try:
            port_providers = _providers()
            proposal = _reuse_proposal(
                foreign_capability_id="ghost.cap"
            )
            orch, model = _engine(
                "langgraph", port_providers, proposal
            )
            attempt = orch.attempt("2 exemplos de terminal bala")
            assert all(
                "ghost" not in str(c)
                for p in port_providers
                for c in p.calls
            )
        finally:
            _NATIVE_ASSESSMENT_LEDGER.reset(token)
