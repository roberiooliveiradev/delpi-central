"""H5 experiment (task DELIA-C3-SEQUENCING-RECOVERY-AB-01): Engine B's
alternative sequencing strategy reuses a previously validated
native_assessment decision during the bounded relevance-recovery
round — but only in the provably safe direction.

Rules under test:

- A prior ``foreign_evidence_required`` decision on the SAME target
  capability + SAME goal is monotonic: an irrelevant native result
  can only strengthen a foreign-evidence requirement, never reduce
  it. Engine B may reuse it and skip the redundant second model call.
- A prior ``sufficient`` decision is REFUTED by the mismatch — it must
  never be reused (the recovery assessment now decides on confirmed
  divergence).
- A changed target (different re-selected capability) invalidates the
  record — reassess.
- Reuse is an opt-in ambient ledger bound by the engine's sequencing
  policy; Engine A never binds it and is byte-for-byte unchanged.
"""

from __future__ import annotations

import pytest

from app.application.capability_provision.orchestration import (
    NATIVE_ASSESSMENT_INSTRUCTION_ID,
    _NATIVE_ASSESSMENT_LEDGER,
)
from app.application.interaction.contracts import (
    LIMITATION_INSUFFICIENT_EVIDENCE,
)
from tests.test_governed_attempt_contract import build_engine
from tests.test_goal_evidence_relevance import (
    ARGUMENTS_INSTRUCTION_ID,
    CAPABILITY_SELECTION_INSTRUCTION_ID,
    GOAL_EVIDENCE_RELEVANCE_INSTRUCTION_ID,
    GROUP_SELECTION_INSTRUCTION_ID,
    FakeProposalModel,
    FakeProvider,
    GovernedCapabilityStatus,
    _cap,
    _cri_clause,
    _doc_cap,
    _doc_outcome,
    _group,
    _outcome,
    _query_cap,
)
_IRRELEVANT = _outcome(
    "ok", structured={"items": [{"name": "BALANCA 1"}]}
)
_RELEVANT = _outcome(
    "ok",
    structured={
        "items": [
            {"name": "TERM. BALA 0,50-2,27MM2"},
            {"name": "TERM. BALA 1,00-2,50MM2"},
        ]
    },
)


def _providers(alpha_outcomes=None, beta_outcome=None):
    pa = FakeProvider(
        "pa",
        [_group("pa", "alpha", [_query_cap()])],
        outcomes={
            ("alpha", "search_items"): (
                alpha_outcomes
                if alpha_outcomes is not None
                else [_IRRELEVANT, _RELEVANT]
            )
        },
    )
    pb = FakeProvider(
        "pb",
        [_group("pb", "beta", [_doc_cap()])],
        outcomes={
            ("beta", "read_guidance"): (
                beta_outcome
                if beta_outcome is not None
                else _doc_outcome()
            )
        },
    )
    return [pa, pb]


def _engine(engine, providers, proposal, **kwargs):
    model = FakeProposalModel(proposal)
    clause = _cri_clause()
    orchestrator = build_engine(
        engine,
        providers=providers,
        model=model,
        response_intelligence_enabled=True,
        cri_instruction_clause=clause.text,
        cri_instruction_version=clause.version,
        **kwargs,
    )
    return orchestrator, model


def _assessment_calls(model):
    return [
        r
        for r in model.requests
        if r.task_purpose_id == NATIVE_ASSESSMENT_INSTRUCTION_ID
    ]


def _select(group_key, remote_name, **extra):
    payload = {
        GROUP_SELECTION_INSTRUCTION_ID: {
            "applicable": True,
            "capability_group_id": group_key,
        },
        CAPABILITY_SELECTION_INSTRUCTION_ID: {
            "applicable": True,
            "remote_name": remote_name,
        },
    }
    payload.update(extra)
    return payload


def _args(arguments):
    return {ARGUMENTS_INSTRUCTION_ID: {"arguments": arguments}}


def _rel(correspondence, hint=None):
    payload = {"correspondence": correspondence}
    if hint:
        payload["mismatch_hint"] = hint
    return {GOAL_EVIDENCE_RELEVANCE_INSTRUCTION_ID: payload}


def _reuse_proposal(
    *,
    first_status="foreign_evidence_required",
    reselect_capability="search_items",
    foreign_capability_id="beta.read_guidance",
    final_correspondence="corresponds",
):
    """Two-group recovery scenario exercising the redundant second
    ``native_assessment`` (H5).

    Call order per unrouted purpose (generic queue):
      admission, turn_goal, native_assessment#1, foreign_selection#1,
      index_probe, native_assessment#2 | foreign_selection#2.

    The assessment/foreign pair is a SINGLE dual-key item so it feeds
    whichever of the two stages consumes it first: a reassessing
    engine pops it as the assessment decision; a reusing engine skips
    the assessment and the same item feeds the foreign selection that
    still runs under the reused decision. Argument slots:
    foreign#1 -> {}, owner#1 -> literal, foreign#2 -> {}, owner#2 ->
    reformulated.
    """
    foreign_round1 = first_status == "foreign_evidence_required"
    select1_args = {} if foreign_round1 else {"query": "terminal bala"}
    proposal = [
        _select(
            "pa:alpha",
            "search_items",
            **_args(select1_args),
            **_rel("irrelevant", "records are scales, not terminals"),
        ),
        _args({"query": "terminal bala"}) if foreign_round1 else None,
        {"goal_class": "record_lookup"},
        {"status": first_status},
        {"foreign_capability_id": foreign_capability_id}
        if foreign_round1
        else {"probe_index": False},
        {"probe_index": False} if foreign_round1 else None,
        _select(
            "pa:alpha",
            reselect_capability,
            **_args({}),
        ),
        {
            "status": "foreign_evidence_required",
            "foreign_capability_id": foreign_capability_id,
        },
        {"foreign_capability_id": foreign_capability_id},
        _args({"query": "TERM. BALA"}),
        _rel(final_correspondence, "still scales" if final_correspondence == "irrelevant" else None),
    ]
    return [item for item in proposal if item is not None]


# ---------------- R1: reusable assessment ----------------


@pytest.mark.parametrize("engine", ["delia", "langgraph_b0", "langgraph"])
def test_r1_prior_foreign_required_is_reused_only_by_strategy(
    engine,
):
    """R1 — equivalent assessment inputs: Engine B (strategy on)
    skips the redundant second native_assessment call; Engine A and
    B0 still pay it. All reach the same business outcome."""
    orch, model = _engine(
        engine, _providers(), _reuse_proposal()
    )
    attempt = orch.attempt("2 exemplos de terminal bala")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert "TERM. BALA" in (attempt.content or "")
    calls = _assessment_calls(model)
    if engine == "langgraph":
        assert len(calls) == 1  # the second decision was reused
    else:
        assert len(calls) == 2


def test_r1_reuse_still_runs_foreign_leg_with_feedback():
    """Reuse skips the decision call, not the evidence consult — the
    recovery foreign leg must still execute under feedback."""
    pa = FakeProvider(
        "pa",
        [_group("pa", "alpha", [_query_cap()])],
        outcomes={
            ("alpha", "search_items"): [_IRRELEVANT, _RELEVANT]
        },
    )
    pb = FakeProvider(
        "pb",
        [_group("pb", "beta", [_doc_cap()])],
        outcomes={("beta", "read_guidance"): _doc_outcome()},
    )
    orch, model = _engine(
        "langgraph", [pa, pb], _reuse_proposal()
    )
    attempt = orch.attempt("2 exemplos de terminal bala")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    # Foreign capability invoked in round 1 AND in the recovery round
    # (the reused decision still routes through the foreign leg).
    assert pb.calls == [
        ("read_guidance", {}),
        ("read_guidance", {}),
    ]


# ---------------- R2: changed premises ----------------


def test_r2_changed_target_invalidates_reuse():
    """R2 — recovery re-selection yields a different capability: the
    prior decision was target-bound, so the assessment must re-run."""
    pa = FakeProvider(
        "pa",
        [
            _group(
                "pa",
                "alpha",
                [
                    _query_cap(),
                    _cap("alpha", "pa", "lookup_items"),
                ],
            )
        ],
        outcomes={
            ("alpha", "search_items"): [_IRRELEVANT],
            ("alpha", "lookup_items"): [_RELEVANT],
        },
    )
    pb = FakeProvider(
        "pb",
        [_group("pb", "beta", [_doc_cap()])],
        outcomes={("beta", "read_guidance"): _doc_outcome()},
    )
    proposal = _reuse_proposal(reselect_capability="lookup_items")
    # Recovery re-selects a different capability -> reassess runs.
    orch, model = _engine("langgraph", [pa, pb], proposal)
    attempt = orch.attempt("2 exemplos de terminal bala")
    assert len(_assessment_calls(model)) == 2
    assert [name for name, _args in pa.calls] == [
        "search_items",
        "lookup_items",
    ]


# ---------------- R3: no reusable prior decision ----------------


def test_r3_sufficient_prior_never_reused():
    """R3 — round-1 'sufficient' was refuted by the mismatch: reuse
    would bypass a mandatory decision on confirmed divergence."""
    orch, model = _engine(
        "langgraph",
        _providers(),
        _reuse_proposal(first_status="sufficient"),
    )
    attempt = orch.attempt("2 exemplos de terminal bala")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert len(_assessment_calls(model)) == 2


# ---------------- R4: relevance honesty ----------------


def test_r4_reuse_cannot_accept_irrelevant_evidence():
    """R4 — even with reuse, a persistently irrelevant owner result
    degrades to honest insufficiency; reuse never fabricates."""
    orch, model = _engine(
        "langgraph",
        _providers(
            alpha_outcomes=[_IRRELEVANT, _IRRELEVANT]
        ),
        _reuse_proposal(final_correspondence="irrelevant"),
    )
    attempt = orch.attempt("2 exemplos de terminal bala")
    assert (
        LIMITATION_INSUFFICIENT_EVIDENCE in attempt.limitations
        or attempt.status is GovernedCapabilityStatus.FAILED
    )


# ---------------- R5: authorization invariance ----------------


def test_r5_reuse_grants_no_authorization():
    """R5 — the reused decision is a string on the sequencing ledger;
    eligibility still flows through live-surface selection and
    candidate tokens. Forging a foreign_capability_id outside the
    live surface cannot resolve — the leg fails closed."""
    proposal = _reuse_proposal(
        foreign_capability_id="ghost.read_guidance"
    )
    pa, pb = _providers()
    orch, model = _engine("langgraph", [pa, pb], proposal)
    attempt = orch.attempt("2 exemplos de terminal bala")
    # The foreign leg failed closed; no ghost invocation occurred.
    assert pb.calls == []
    # Owner re-invocation still governed — the forged id never leaks
    # into the presented answer or its provenance.
    assert "ghost" not in (attempt.content or "")
    assert "ghost" not in str(attempt.provenance or "")


def test_r5b_candidate_token_opacity_preserved_under_reuse():
    """R5 — reuse never leaks capability identifiers or candidate
    tokens into the presented answer (token opacity invariant)."""
    orch, model = _engine(
        "langgraph", _providers(), _reuse_proposal()
    )
    attempt = orch.attempt("2 exemplos de terminal bala")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert "search_items" not in (attempt.content or "")
    assert "remote_name" not in (attempt.content or "")


# ---------------- R6: cancellation ----------------


def test_r6_cancellation_overrides_reuse():
    """R6 — cancellation short-circuits before any optimization."""
    orch, model = _engine(
        "langgraph",
        _providers(),
        _reuse_proposal(),
    )
    attempt = orch.attempt(
        "2 exemplos de terminal bala", cancel_check=lambda: True
    )
    assert attempt.status is GovernedCapabilityStatus.PROCESSING_TIMEOUT


# ---------------- R7: recovery boundedness ----------------


def test_r7_recovery_ceiling_unchanged_under_reuse():
    """R7 — reuse changes a decision's provenance, not the recovery
    ceiling: still at most one bounded recovery round (2 invokes)."""
    pa = FakeProvider(
        "pa",
        [_group("pa", "alpha", [_query_cap()])],
        outcomes={
            ("alpha", "search_items"): [
                _IRRELEVANT,
                _IRRELEVANT,
                _IRRELEVANT,
            ]
        },
    )
    pb = FakeProvider(
        "pb",
        [_group("pb", "beta", [_doc_cap()])],
        outcomes={("beta", "read_guidance"): _doc_outcome()},
    )
    proposal = _reuse_proposal(final_correspondence="irrelevant")
    orch, model = _engine("langgraph", [pa, pb], proposal)
    attempt = orch.attempt("2 exemplos de terminal bala")
    assert len(pa.calls) == 2
    assert "insufficient_evidence" in attempt.limitations


# ---------------- R8: traceability ----------------


def test_r8_trace_marks_reused_decision():
    """R8 — the graph trace records whether the recovery assessment
    was reused or reassessed (no secrets, no chain-of-thought)."""
    orch, model = _engine(
        "langgraph", _providers(), _reuse_proposal()
    )
    attempt = orch.attempt("2 exemplos de terminal bala")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    trace = orch.last_node_trace
    assert "evidence_session" in trace
    assert "assessment_reused" in trace


def test_r8_trace_marks_reassessed_when_premises_differ():
    """R8 — with a 'sufficient' prior the trace shows a genuine
    reassessment, not a silent skip."""
    orch, model = _engine(
        "langgraph",
        _providers(),
        _reuse_proposal(first_status="sufficient"),
    )
    attempt = orch.attempt("2 exemplos de terminal bala")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    trace = orch.last_node_trace
    assert "assessment_reassessed" in trace
    assert "assessment_reused" not in trace


# ---------------- R9: Engine A isolation ----------------


def test_r9_engine_a_behavior_unchanged():
    """R9 — Engine A never binds the ledger: same fixture, same call
    counts and outcome as before the strategy existed."""
    pa, pb = _providers()
    orch, model = _engine("delia", [pa, pb], _reuse_proposal())
    attempt = orch.attempt("2 exemplos de terminal bala")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert len(_assessment_calls(model)) == 2
    # No reuse trace leaks into Engine A.
    assert not hasattr(orch, "last_node_trace")


def test_r9b_engine_b_baseline_without_strategy_pays_both_calls():
    """R9/B0 — Engine B with the strategy flag off is the honest
    framework baseline: identical calls to Engine A."""
    pa, pb = _providers()
    orch, model = _engine(
        "langgraph_b0", [pa, pb], _reuse_proposal()
    )
    attempt = orch.attempt("2 exemplos de terminal bala")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert len(_assessment_calls(model)) == 2


# ---------------- R10: actual alternative transition ----------------


def test_r10_strategy_produces_visible_alternative_transition():
    """R10 — the strategy is a real graph-level divergence: the B1
    trace carries the reuse decision event while B0's identical run
    does not."""
    orch1, _ = _engine(
        "langgraph", _providers(), _reuse_proposal()
    )
    orch0, _ = _engine(
        "langgraph_b0", _providers(), _reuse_proposal()
    )
    a1 = orch1.attempt("2 exemplos de terminal bala")
    a0 = orch0.attempt("2 exemplos de terminal bala")
    t1 = orch1.last_node_trace
    t0 = orch0.last_node_trace
    assert "assessment_reused" in t1
    assert "assessment_reused" not in t0
    # Same governed outcome either way.
    assert a1.status == a0.status == GovernedCapabilityStatus.SUCCESS


# ---------------- ledger mechanics ----------------


def test_ledger_is_none_by_default():
    """Ambient opt-in: without a bound ledger nothing changes."""
    assert _NATIVE_ASSESSMENT_LEDGER.get() is None


def test_engine_b_does_not_construct_engine_a():
    """Regression guard — the adapter still delegates to injected
    gates only (strategies don't re-couple to Engine A)."""
    import app.infrastructure.orchestration.langgraph_engine as mod
    import ast
    import inspect

    tree = ast.parse(inspect.getsource(mod))
    names = {
        getattr(node, "id", getattr(node, "attr", None))
        for node in ast.walk(tree)
    }
    assert "OperationalCapabilityOrchestrator" not in names
