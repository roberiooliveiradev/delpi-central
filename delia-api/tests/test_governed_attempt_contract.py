"""DELIA-C3-PLUGGABLE-ORCHESTRATION-CONTRACT-FOUNDATION-01 — reusable
SupportsGovernedCapabilityAttempt conformance suite (doc 192/193).

Every test exercises only the application boundary:

    engine.attempt(input_text, *, correlation_id, actor_user_id,
        session_id, confirmation, workspace_context, prior_turns,
        max_execution_stage, turn_deadline, activity_sink,
        cancel_check) -> GovernedCapabilityAttempt

Assertions observe boundary-visible truth only — status, error_code,
content, provenance, confirmation_context and owner-port calls —
never orchestrator-internal stage names, methods or state.

``ENGINE_IDS`` is the registry of implementations under contract.
Today only ``delia`` exists; a future authorized engine adds an id and
a ``build_engine`` branch — no test changes.

Proposal payloads are per-engine model-stub scripts supplied through
``build_engine`` — the contract suite asserts what the engine must
DO given a scenario, not how it sequences the model stages that
produce it.
"""

from __future__ import annotations

import inspect
import json

import pytest

from app.application.interaction.capability_attempt import (
    GovernedCapabilityStatus,
    SupportsGovernedCapabilityAttempt,
)
from app.application.interaction.turn_budget import TurnDeadline
from app.application.model_invocation.invoke_model import InvokeModel
from app.application.capability_provision.mcp_provider import (
    McpCapabilityProvider,
)
from app.application.capability_provision.orchestration import (
    ARGUMENTS_INSTRUCTION_ID,
    INTERACTION_ADMISSION_INSTRUCTION_ID,
    OperationalCapabilityOrchestrator,
)
from app.application.specialist_interop.contracts import RemoteToolOutcome
from app.application.specialist_interop.errors import (
    MCP_AUTHORIZATION_DENIED,
    SpecialistInteropError,
)
from app.domain.evidence.model import EpistemicClass

from tests.conftest import load_test_orchestration_instructions
from tests.test_specialist_capability_orchestration import (
    COMMIT_VERIFIED,
    DAVI_TOOLS,
    DISCOVERY_RESULT,
    FakePort,
    FakeProposalModel,
    READY_PROPOSAL,
    TEO_TOOLS,
    VISTA_TOOLS,
    _confirmation,
    _interop,
    _select,
)
from tests.test_execution_ceiling_turn_budget import (
    TEST_MODEL_REF,
    _StageModel,
)
from tests.test_governed_stage_resume import _FlakyStageModel


# --- engine registry (one entry per SupportsGovernedCapabilityAttempt
# implementation authorized for the boundary) -------------------------

ENGINE_IDS: tuple[str, ...] = ("delia", "langgraph")


def _build_langgraph_engine(
    *,
    port: FakePort,
    specialist_ids: tuple[str, ...],
    proposal=None,
    model=None,
    providers=None,
    turn_budget_seconds=None,
    max_governed_attempts=1,
    llm_call_max_attempts=1,
    recovery_reuse_enabled=True,
    **gates_kwargs,
) -> SupportsGovernedCapabilityAttempt:
    """Engine B — LangGraph sequencing over the same governed
    primitives. Skipped entirely when the optional eval dependency is
    absent (never a production requirement). ``recovery_reuse_enabled``
    toggles the H5 sequencing strategy (B1 vs the B0 framework
    baseline) — a sequencing knob, never a production setting."""
    pytest.importorskip("langgraph")
    from app.infrastructure.orchestration.langgraph_engine import (
        LangGraphCapabilityOrchestrator,
    )

    if providers is None:
        providers = [McpCapabilityProvider(_interop(port), specialist_ids)]
    if model is None and proposal is not None:
        model = FakeProposalModel(proposal)
    invoke_model = InvokeModel(model) if model is not None else None
    kwargs = {}
    if turn_budget_seconds is not None:
        kwargs["turn_budget_seconds"] = turn_budget_seconds
    # Composition is a harness concern: the same governed-primitives
    # provider instance Engine A would run is injected through the
    # application-owned gates contract — the adapter never constructs
    # or imports it (doc 195, F2).
    gates = OperationalCapabilityOrchestrator(
        providers,
        orchestration_instructions=load_test_orchestration_instructions(),
        invoke_model=invoke_model,
        model_ref=TEST_MODEL_REF if invoke_model else None,
        max_governed_attempts=max_governed_attempts,
        llm_call_max_attempts=llm_call_max_attempts,
        **gates_kwargs,
        **kwargs,
    )
    return LangGraphCapabilityOrchestrator(
        gates,
        recovery_reuse_enabled=recovery_reuse_enabled,
    )


def build_engine(
    engine_id: str,
    *,
    port=None,
    specialist_ids: tuple[str, ...] = (),
    proposal=None,
    model=None,
    providers=None,
    turn_budget_seconds=None,
    max_governed_attempts=1,
    llm_call_max_attempts=1,
    **gates_kwargs,
) -> SupportsGovernedCapabilityAttempt:
    """Construct the governed-attempt implementation under test.

    Per-engine wiring lives ONLY here: each id maps the shared fake
    owner surface and its own model-stub scripts onto the same attempt
    boundary. Contract tests below never see engine internals.

    ``providers`` overrides the FakePort→McpCapabilityProvider wiring
    for scenarios that need richer provider-level fixtures (relevance
    judgments, typed outcomes). ``turn_budget_seconds`` defaults to
    the implementation default — a smaller budget legitimately
    changes behavior (optional probes are skipped for headroom), so
    tests that need a bounded window pass ``turn_deadline`` on
    ``attempt()`` instead.
    """
    if engine_id in ("langgraph", "langgraph_b0"):
        return _build_langgraph_engine(
            port=port,
            specialist_ids=specialist_ids,
            proposal=proposal,
            model=model,
            providers=providers,
            turn_budget_seconds=turn_budget_seconds,
            max_governed_attempts=max_governed_attempts,
            llm_call_max_attempts=llm_call_max_attempts,
            recovery_reuse_enabled=(engine_id == "langgraph"),
            **gates_kwargs,
        )
    if engine_id != "delia":
        raise AssertionError(f"unregistered engine {engine_id!r}")
    if providers is None:
        providers = [McpCapabilityProvider(_interop(port), specialist_ids)]
    if model is None and proposal is not None:
        model = FakeProposalModel(proposal)
    invoke_model = InvokeModel(model) if model is not None else None
    kwargs = {}
    if turn_budget_seconds is not None:
        kwargs["turn_budget_seconds"] = turn_budget_seconds
    return OperationalCapabilityOrchestrator(
        providers,
        orchestration_instructions=load_test_orchestration_instructions(),
        invoke_model=invoke_model,
        model_ref=TEST_MODEL_REF if invoke_model else None,
        max_governed_attempts=max_governed_attempts,
        llm_call_max_attempts=llm_call_max_attempts,
        **gates_kwargs,
        **kwargs,
    )


@pytest.fixture(params=ENGINE_IDS)
def engine_id(request):
    return request.param


# --- boundary signature parity -----------------------------------------


def test_attempt_signature_parity_with_runtime(engine_id):
    """The Protocol the handler consumes must faithfully declare every
    argument the boundary supports — no undeclared kwargs and none the
    implementation lacks. Parity is over parameter NAMES and defaults
    only: a different engine may type a sink differently."""
    proto = inspect.signature(
        SupportsGovernedCapabilityAttempt.attempt
    ).parameters
    impl = inspect.signature(
        OperationalCapabilityOrchestrator.attempt
    ).parameters
    proto = {k: v for k, v in proto.items() if k != "self"}
    impl = {k: v for k, v in impl.items() if k != "self"}
    assert set(proto) == set(impl), (
        f"protocol/impl mismatch: "
        f"missing={sorted(set(impl) - set(proto))} "
        f"extra={sorted(set(proto) - set(impl))}"
    )
    for name, impl_param in impl.items():
        assert proto[name].kind is impl_param.kind, name
        assert proto[name].default == impl_param.default, name


# --- READ selection + execution -----------------------------------------


def test_read_selected_invoked_and_projected(engine_id):
    """An applicable read proposal selects, invokes the owner READ and
    surfaces a SUCCESS attempt with authoritative provenance."""
    port = FakePort(tools_by_specialist={"teo": TEO_TOOLS})
    engine = build_engine(
        engine_id,
        port=port,
        specialist_ids=("teo",),
        proposal=_select("teo", "analyze", {"view": "summary"}),
    )
    attempt = engine.attempt("Resumo dos indicadores")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert attempt.outcome.epistemic_class is EpistemicClass.OBSERVATION
    assert attempt.provenance.specialist_id == "teo"
    assert attempt.provenance.remote_capability == "analyze"
    assert attempt.provenance.protocol == "MCP"
    assert attempt.provenance.correlation_id == attempt.correlation_id
    assert attempt.content
    assert port.calls == [("teo", "analyze", {"view": "summary"})]


def test_no_model_fails_closed(engine_id):
    """Without a selection model the engine returns NOT_APPLICABLE and
    performs no owner call — never an invented answer."""
    port = FakePort(tools_by_specialist={"teo": TEO_TOOLS})
    engine = build_engine(
        engine_id, port=port, specialist_ids=("teo",)
    )
    attempt = engine.attempt("Resumo dos indicadores")
    assert attempt.status is GovernedCapabilityStatus.NOT_APPLICABLE
    assert port.calls == []


# --- structured goal + candidate binding ---------------------------------


def test_candidate_bound_read_end_to_end(engine_id):
    """Discovery -> owner-issued candidate -> candidate-bound READ:
    the token is owner-issued, never model-supplied."""
    port = FakePort(
        tools_by_specialist={"davi": DAVI_TOOLS},
        outcomes={"discover_delpi_information": DISCOVERY_RESULT},
    )
    engine = build_engine(
        engine_id,
        port=port,
        specialist_ids=("davi",),
        proposal=_select(
            "davi", "execute_delpi_information",
            {"arguments": {"description": "tubo"}},
        ),
    )
    attempt = engine.attempt("Procure produtos DELPI sobre tubo")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert [c[1] for c in port.calls] == [
        "discover_delpi_information",
        "execute_delpi_information",
    ]
    exec_call = port.calls[1]
    assert exec_call[2]["candidate_token"] == "tok-owner-issued"


def test_candidate_token_model_supplied_rejected(engine_id):
    """A proposal carrying a forged candidate_token fails closed —
    no owner call is ever made."""
    port = FakePort(
        tools_by_specialist={"davi": DAVI_TOOLS},
        outcomes={"discover_delpi_information": DISCOVERY_RESULT},
    )
    engine = build_engine(
        engine_id,
        port=port,
        specialist_ids=("davi",),
        proposal=_select(
            "davi", "execute_delpi_information",
            {"candidate_token": "forged",
             "arguments": {"description": "tubo"}},
        ),
    )
    attempt = engine.attempt("produtos tubo")
    assert attempt.status is GovernedCapabilityStatus.NOT_APPLICABLE
    assert port.calls == []


def test_multi_candidate_requires_selection(engine_id):
    """A discovery surface with several owner candidates never
    silently picks one without the governed selection stage."""
    port = FakePort(
        tools_by_specialist={"davi": DAVI_TOOLS},
        outcomes={
            "discover_delpi_information": RemoteToolOutcome(
                content_text="{}",
                structured={
                    "candidates": [
                        {"candidate_token": "a"},
                        {"candidate_token": "b"},
                    ]
                },
            )
        },
    )
    engine = build_engine(
        engine_id,
        port=port,
        specialist_ids=("davi",),
        proposal=_select(
            "davi", "execute_delpi_information",
            {"arguments": {"description": "tubo"}},
        ),
    )
    attempt = engine.attempt("produtos tubo")
    # Fails closed after discovery — no uninformed execute.
    assert attempt.status is not GovernedCapabilityStatus.SUCCESS
    assert [c[1] for c in port.calls] == ["discover_delpi_information"]


# --- discovery + argument validation -------------------------------------


def test_arguments_bounded_to_owner_schema(engine_id):
    """Proposed keys outside the owner schema invalidate — the execute
    call is never reached."""
    port = FakePort(
        tools_by_specialist={"davi": DAVI_TOOLS},
        outcomes={"discover_delpi_information": DISCOVERY_RESULT},
    )
    engine = build_engine(
        engine_id,
        port=port,
        specialist_ids=("davi",),
        proposal=_select(
            "davi", "execute_delpi_information",
            {"arguments": {"description": "tubo", "injected": "x"}},
        ),
    )
    attempt = engine.attempt("produtos tubo")
    assert attempt.status is not GovernedCapabilityStatus.SUCCESS
    assert [c[1] for c in port.calls] == ["discover_delpi_information"]


# --- owner errors + unauthorized capability ------------------------------


def test_owner_authz_denied_propagates(engine_id):
    """Owner authorization failure surfaces AUTHZ_DENIED — typed,
    truthful, never synthesized as success."""
    port = FakePort(
        tools_by_specialist={"vista": VISTA_TOOLS},
        errors={
            ("vista", "list_playlists"): SpecialistInteropError(
                MCP_AUTHORIZATION_DENIED, "denied"
            )
        },
    )
    engine = build_engine(
        engine_id,
        port=port,
        specialist_ids=("vista",),
        proposal=_select("vista", "list_playlists"),
    )
    attempt = engine.attempt("liste minhas playlists")
    assert attempt.status is GovernedCapabilityStatus.AUTHZ_DENIED
    assert attempt.error_code


def test_invented_capability_fails_closed(engine_id):
    """A model proposal naming a capability the owner does not
    advertise fails closed — eligibility is never model-decided."""
    port = FakePort(tools_by_specialist={"teo": TEO_TOOLS})
    engine = build_engine(
        engine_id,
        port=port,
        specialist_ids=("teo",),
        proposal=_select("teo", "does_not_exist"),
    )
    attempt = engine.attempt("qualquer coisa")
    # Engine-neutral refusal: no SUCCESS and no owner call. The
    # concrete truthful status (NOT_APPLICABLE vs
    # CLARIFICATION_REQUIRED ask-back) is implementation detail.
    assert attempt.status is not GovernedCapabilityStatus.SUCCESS
    assert not [c for c in port.calls if c[1] == "does_not_exist"]


# --- PREPARE/ACT + confirmation ------------------------------------------


def test_prepare_act_governance_and_confirmation(engine_id):
    """PREPARE surfaces a bounded confirmation gate (digests only);
    CONFIRM resumes and invokes the owner ACT exactly once."""
    port = FakePort(
        tools_by_specialist={"vista": VISTA_TOOLS},
        outcomes={
            "prepare_change": READY_PROPOSAL,
            "commit_proposal": COMMIT_VERIFIED,
        },
    )
    engine = build_engine(
        engine_id,
        port=port,
        specialist_ids=("vista",),
        proposal=_select(
            "vista", "prepare_change", {"record_id": "p1"},
            goal_class="create_or_modify",
        ),
    )
    pending = engine.attempt(
        "Altere o nome do painel p1 para Painel X",
        actor_user_id="u1",
        session_id="s1",
    )
    assert pending.status is (
        GovernedCapabilityStatus.CONFIRMATION_REQUIRED
    )
    # Raw handle never leaves the backend.
    assert "prop-handle-1" not in json.dumps(
        pending.confirmation_context
    )
    assert "prop-handle-1" not in pending.content
    # No ACT before confirmation.
    assert not [c for c in port.calls if c[1] == "commit_proposal"]

    result = engine.attempt(
        "",
        actor_user_id="u1",
        confirmation=_confirmation(pending),
    )
    assert result.status is GovernedCapabilityStatus.SUCCESS
    commit = [c for c in port.calls if c[1] == "commit_proposal"]
    assert len(commit) == 1


def test_act_never_invocable_without_pending_proposal(engine_id):
    """An ACT selection with no pending proposal refuses truthfully —
    no wire call."""
    port = FakePort(tools_by_specialist={"vista": VISTA_TOOLS})
    engine = build_engine(
        engine_id,
        port=port,
        specialist_ids=("vista",),
        proposal=_select(
            "vista", "commit_proposal", goal_class="create_or_modify"
        ),
    )
    attempt = engine.attempt("confirme a alteração")
    assert attempt.status is GovernedCapabilityStatus.WRITE_REJECTED
    assert port.calls == []


# --- budget / timeout / cancellation --------------------------------------


def test_model_timeout_is_processing_timeout(engine_id):
    """Model-stage timeouts exhaust the retry budget and terminate as
    PROCESSING_TIMEOUT with model_timeout error — never blamed on the
    owner source."""
    model = _FlakyStageModel(
        proposals=_select("teo", "analyze", {"view": "summary"}),
        failures={ARGUMENTS_INSTRUCTION_ID: 3},
    )
    port = FakePort(tools_by_specialist={"teo": TEO_TOOLS})
    engine = build_engine(
        engine_id,
        port=port,
        specialist_ids=("teo",),
        model=model,
        llm_call_max_attempts=3,
    )
    attempt = engine.attempt(
        "resumo", turn_deadline=TurnDeadline.start(30.0)
    )
    assert attempt.status is GovernedCapabilityStatus.PROCESSING_TIMEOUT
    assert attempt.error_code == "model_timeout"
    assert port.calls == []


def test_cancel_check_from_start_is_terminal(engine_id):
    """Cancellation observed at the boundary is terminal: no model
    invocation starts, PROCESSING_TIMEOUT with cancelled cause."""
    model = _StageModel(
        proposals=_select("teo", "analyze", {"view": "summary"})
    )
    port = FakePort(tools_by_specialist={"teo": TEO_TOOLS})
    engine = build_engine(
        engine_id,
        port=port,
        specialist_ids=("teo",),
        model=model,
    )
    attempt = engine.attempt(
        "resumo",
        turn_deadline=TurnDeadline.start(30.0),
        cancel_check=lambda: True,
    )
    assert attempt.status is GovernedCapabilityStatus.PROCESSING_TIMEOUT
    assert attempt.error_code == "cancelled"
    assert model.requests == []


# --- telemetry / return-status observables ---------------------------------


def test_correlation_id_round_trips(engine_id):
    """A supplied correlation id is preserved verbatim on the returned
    attempt and its provenance."""
    port = FakePort(tools_by_specialist={"teo": TEO_TOOLS})
    engine = build_engine(
        engine_id,
        port=port,
        specialist_ids=("teo",),
        proposal=_select("teo", "analyze", {"view": "summary"}),
    )
    attempt = engine.attempt("analise", correlation_id="corr-1")
    assert attempt.correlation_id == "corr-1"
    assert attempt.provenance.correlation_id == "corr-1"


# --- Engine-B-specific: real graph, non-delegation, isolation ----------


@pytest.fixture
def langgraph_engine():
    pytest.importorskip("langgraph")
    return _build_langgraph_engine(
        port=FakePort(tools_by_specialist={"teo": TEO_TOOLS}),
        specialist_ids=("teo",),
        proposal=_select("teo", "analyze", {"view": "summary"}),
    )


def test_engine_b_executes_real_graph_nodes(langgraph_engine):
    """A genuine implementation runs real LangGraph nodes/edges — the
    engine records the executed node trace per invocation. A wrapper
    delegating to attempt() produces no node trace."""
    from langgraph.graph.state import CompiledStateGraph

    assert isinstance(
        langgraph_engine._compiled_graph, CompiledStateGraph
    )
    attempt = langgraph_engine.attempt("resumo dos indicadores")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    trace = langgraph_engine.last_node_trace
    # Real sequencing: preflight -> admission routing -> owner path.
    assert trace[0] == "preflight"
    assert "admission" in trace
    assert trace[-1] == "owner_path"


def test_engine_b_never_delegates_to_engine_a(langgraph_engine):
    """If OperationalCapabilityOrchestrator._attempt were called, this
    spy would record it — Engine B must sequence governed primitives
    itself, never delegate the complete flow."""
    calls = []
    original = OperationalCapabilityOrchestrator._attempt

    def _spy(self, *args, **kwargs):
        calls.append(1)
        return original(self, *args, **kwargs)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            OperationalCapabilityOrchestrator, "_attempt", _spy
        )
        attempt = langgraph_engine.attempt("resumo dos indicadores")
    assert calls == [], "Engine B delegated to Engine A _attempt"
    assert attempt.status is GovernedCapabilityStatus.SUCCESS


def test_engine_b_uses_shared_governed_primitives(langgraph_engine):
    """Engine B must consume the SAME governed machinery — no
    duplicated validation, selection, invoke or synthesis logic."""
    import inspect as _inspect
    import app.infrastructure.orchestration.langgraph_engine as mod

    src = _inspect.getsource(mod)
    # The engine module must not re-implement governed gates.
    for forbidden in (
        "def _validate_instance",
        "def _propose(",
        "def _select_group",
        "def _select_capability",
        "def _invoke(",
        "def _candidate_arguments",
        "def _judge_goal_evidence",
        "def _synthesize_content",
        "def _recover_relevance",
        "def _attempt_prepare",
        "def _attempt_confirmation",
    ):
        assert forbidden not in src, (
            f"Engine B duplicates governed gate: {forbidden}"
        )


def test_engine_b_not_wired_in_production_composer():
    """Engine B is local-evaluation only — the production composer
    must not reference it, nor an engine selector."""
    from pathlib import Path

    src = (
        Path(__file__).resolve().parent.parent
        / "app"
        / "composition"
        / "root_composer.py"
    ).read_text()
    assert "langgraph" not in src.lower()
    assert "LangGraphCapabilityOrchestrator" not in src


def test_langgraph_not_in_production_requirements():
    """The eval dependency stays out of the productive requirement
    set — Engine B is opt-in local test infrastructure."""
    from pathlib import Path

    req = (
        Path(__file__).resolve().parent.parent / "requirements.txt"
    ).read_text().lower()
    assert "langgraph" not in req
    assert "langchain" not in req


# --- doc-192 scenario matrix (S2, S3, S4, S6, S7) ---------------------
# Provider-level fixtures from test_goal_evidence_relevance enable the
# goal/evidence judgment and recovery stages the FakePort harness
# cannot express. All boundary-only assertions.


from app.application.capability_provision.orchestration import (
    GOAL_EVIDENCE_RELEVANCE_INSTRUCTION_ID,
    GOAL_INSTRUCTION_ID,
    LIMITATION_INSUFFICIENT_EVIDENCE,
    SYNTHESIS_INSTRUCTION_ID,
)
from app.application.model_invocation.contracts import (
    ConversationContextTurn,
)
from app.application.specialist_interop.errors import SPECIALIST_DISABLED
from app.domain.interaction.model import TurnKind
from tests.test_goal_evidence_relevance import (
    FakeProvider,
    FakeProposalModel as _RelevanceProposalModel,
    _cri_clause,
    _cap,
    _group,
    _outcome,
    _select as _rel_select,
)


_QUERY_SCHEMA = {
    "type": "object",
    "properties": {"query": {"type": "string"}},
}


def _items_provider(items_or_queue):
    cap = _cap("alpha", "mcp", "search_items", schema=_QUERY_SCHEMA)
    return FakeProvider(
        "mcp",
        [_group("mcp", "alpha", [cap])],
        outcomes={("alpha", "search_items"): items_or_queue},
    )


def test_s2_two_matching_records_with_codes(engine_id):
    """S2: two correct owner records — both codes surface verbatim."""
    provider = _items_provider(
        _outcome(
            "ok",
            structured={
                "data": {
                    "items": [
                        {"code": "10080092",
                         "description": "TERM. BALA 0,50-2,27MM2"},
                        {"code": "10081004",
                         "description": "TERM. BALA 1,00-2,50MM2"},
                    ]
                }
            },
        )
    )
    engine = build_engine(
        engine_id,
        providers=[provider],
        proposal=_rel_select(
            "mcp:alpha", "search_items",
            args={"arguments": {"query": "terminal bala"}},
        ),
    )
    attempt = engine.attempt("Dois exemplos de terminal bala")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert "10080092" in attempt.content
    assert "10081004" in attempt.content
    assert provider.calls


def test_s3_irrelevant_result_bounded_recovery(engine_id):
    """S3: first result irrelevant to the goal -> ONE governed
    recovery round -> reformulated invoke -> truthful SUCCESS."""
    irrelevant = _outcome(
        "ok", structured={"items": [{"name": "BALANCA 1"}]}
    )
    relevant = _outcome(
        "ok",
        structured={
            "items": [{"name": "TERMINAL ILHOS TUBULAR 16MM"}]
        },
    )
    provider = _items_provider([irrelevant, relevant])
    proposal = [
        _rel_select(
            "mcp:alpha", "search_items",
            args={"arguments": {"query": "terminal"}},
            relevance=None,
        ),
        {
            GOAL_EVIDENCE_RELEVANCE_INSTRUCTION_ID: {
                "correspondence": "irrelevant",
                "mismatch_hint": "records are not terminals",
            }
        },
        {
            ARGUMENTS_INSTRUCTION_ID: {
                "arguments": {"query": "terminal ilhos tubular"}
            }
        },
        {
            GOAL_EVIDENCE_RELEVANCE_INSTRUCTION_ID: {
                "correspondence": "corresponds",
            }
        },
    ]
    clause = _cri_clause()
    engine = build_engine(
        engine_id,
        providers=[provider],
        model=_RelevanceProposalModel(proposal),
        response_intelligence_enabled=True,
        cri_instruction_clause=clause.text,
        cri_instruction_version=clause.version,
    )
    attempt = engine.attempt("terminal tubular")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    # Bounded: exactly two invokes — initial + one recovery re-invoke.
    assert len(provider.calls) == 2


def test_s4_no_records_never_fabricates(engine_id):
    """S4: owner returns non-matching records in both rounds —
    insufficiency is reported truthfully, never inventing codes or
    record content."""
    wrong_a = _outcome(
        "ok", structured={"items": [{"name": "BALANCA 1"}]}
    )
    wrong_b = _outcome(
        "ok", structured={"items": [{"name": "BALANCA 2"}]}
    )
    provider = _items_provider([wrong_a, wrong_b])
    proposal = [
        _rel_select(
            "mcp:alpha", "search_items",
            args={"arguments": {"query": "terminal bala"}},
            relevance=None,
        ),
        {
            GOAL_EVIDENCE_RELEVANCE_INSTRUCTION_ID: {
                "correspondence": "irrelevant",
                "mismatch_hint": "scales, not bullet terminals",
            }
        },
        {
            ARGUMENTS_INSTRUCTION_ID: {
                "arguments": {"query": "terminal bala registro"}
            }
        },
        {
            GOAL_EVIDENCE_RELEVANCE_INSTRUCTION_ID: {
                "correspondence": "irrelevant",
                "mismatch_hint": "still scales",
            }
        },
    ]
    clause = _cri_clause()
    engine = build_engine(
        engine_id,
        providers=[provider],
        model=_RelevanceProposalModel(proposal),
        response_intelligence_enabled=True,
        cri_instruction_clause=clause.text,
        cri_instruction_version=clause.version,
    )
    attempt = engine.attempt("registros de terminal bala")
    # Truthful non-success OR success explicitly limited — never an
    # unqualified records answer.
    assert (
        attempt.status is not GovernedCapabilityStatus.SUCCESS
        or LIMITATION_INSUFFICIENT_EVIDENCE in attempt.limitations
    )
    for fabricated in ("10080092", "10081004"):
        assert fabricated not in (attempt.content or "")


def test_s6_prior_context_continuation_no_reinvoke(engine_id):
    """S6: a prior OBSERVATION turn + goal declaring prior evidence
    sufficient continues from context — no new owner invocation."""
    prior = (
        ConversationContextTurn(
            kind=TurnKind.USER_INPUT,
            content="liste os painéis",
        ),
        ConversationContextTurn(
            kind=TurnKind.DELIA_RESULT,
            content="1. Painel A\n2. Painel B",
            epistemic_class=EpistemicClass.OBSERVATION,
        ),
    )
    proposal = {
        INTERACTION_ADMISSION_INSTRUCTION_ID: {
            "requires_owner_surface": True,
            "interaction_class": "operational",
        },
        GOAL_INSTRUCTION_ID: {
            "goal_class": "read",
            "prior_evidence_sufficient": True,
        },
        SYNTHESIS_INSTRUCTION_ID: {
            "items": [{"record_index": 0, "fields": ["excerpt"]}]
        },
    }
    port = FakePort(tools_by_specialist={"teo": TEO_TOOLS})
    engine = build_engine(
        engine_id,
        port=port,
        specialist_ids=("teo",),
        proposal=proposal,
    )
    attempt = engine.attempt("e o terceiro?", prior_turns=prior)
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    # Continuity: no owner capability invoked this turn.
    assert port.calls == []


def test_s7_owner_unavailable_truthful_failure(engine_id):
    """S7: owner unreachable/disabled -> SOURCE_UNAVAILABLE, no
    invented evidence."""
    port = FakePort(
        tools_by_specialist={"teo": TEO_TOOLS},
        errors={
            ("teo", "analyze"): SpecialistInteropError(
                SPECIALIST_DISABLED, "off"
            )
        },
    )
    engine = build_engine(
        engine_id,
        port=port,
        specialist_ids=("teo",),
        proposal=_select("teo", "analyze"),
    )
    attempt = engine.attempt("resumo")
    assert attempt.status is GovernedCapabilityStatus.SOURCE_UNAVAILABLE
    # Fail-closed truth: the owner call errored, no fabricated data.
    assert "100" not in (attempt.content or "")
