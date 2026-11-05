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

# Owner-path contract matrix stays on Application sequencer (`delia`).
# Pydantic AI investigation is covered by dedicated rework/runtime
# suites — it must not silently re-enter ``_governed_owner_path``.
ENGINE_IDS: tuple[str, ...] = ("delia",)


def _build_pydantic_ai_engine(
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
    investigation_model=None,
    **gates_kwargs,
) -> SupportsGovernedCapabilityAttempt:
    """Pydantic AI investigation runtime over shared governed gates."""
    from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart
    from pydantic_ai.models.function import FunctionModel
    from app.application.interaction.turn_budget import TurnDeadline
    from app.infrastructure.orchestration.pydantic_ai_investigation import (
        PydanticAiInvestigationOrchestrator,
    )

    if providers is None:
        providers = [McpCapabilityProvider(_interop(port), specialist_ids)]
    if model is None and proposal is not None:
        model = FakeProposalModel(proposal)
    invoke_model = InvokeModel(model) if model is not None else None
    kwargs = {}
    if turn_budget_seconds is not None:
        kwargs["turn_budget_seconds"] = turn_budget_seconds
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
    if investigation_model is None:
        catalog = gates._project_semantic_tool_catalog(
            correlation="test-build",
            deadline=TurnDeadline.start(30.0),
        )
        read_caps = [
            entry
            for entry in catalog
            if entry.get("operation_class") == "READ"
        ]
        cap_id = (
            str(read_caps[0]["capability_id"]) if read_caps else ""
        )

        def _scripted_agent(messages, _info):
            if not any(isinstance(m, ModelResponse) for m in messages):
                return ModelResponse(
                    parts=[
                        ToolCallPart(
                            "invoke_read_capability",
                            {
                                "capability_id": cap_id,
                                "arguments": {},
                            },
                        )
                    ]
                )
            return ModelResponse(parts=[TextPart("done")])

        investigation_model = FunctionModel(_scripted_agent)
    return PydanticAiInvestigationOrchestrator(
        gates,
        model=investigation_model,
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
    """
    if engine_id == "pydantic_ai":
        return _build_pydantic_ai_engine(
            port=port,
            specialist_ids=specialist_ids,
            proposal=proposal,
            model=model,
            providers=providers,
            turn_budget_seconds=turn_budget_seconds,
            max_governed_attempts=max_governed_attempts,
            llm_call_max_attempts=llm_call_max_attempts,
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


# --- Pydantic AI investigation runtime: sequencing + isolation --------


@pytest.fixture
def pydantic_ai_engine():
    return _build_pydantic_ai_engine(
        port=FakePort(tools_by_specialist={"teo": TEO_TOOLS}),
        specialist_ids=("teo",),
        proposal=_select("teo", "analyze", {"view": "summary"}),
    )


def test_pydantic_ai_records_stage_trace(pydantic_ai_engine):
    attempt = pydantic_ai_engine.attempt("resumo dos indicadores")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    trace = pydantic_ai_engine.last_node_trace
    assert trace[0] == "preflight"
    assert "admission" in trace
    assert "investigation" in trace


def test_pydantic_ai_never_delegates_to_application_attempt(
    pydantic_ai_engine,
):
    calls = []
    original = OperationalCapabilityOrchestrator._attempt

    def _spy(self, *args, **kwargs):
        calls.append(1)
        return original(self, *args, **kwargs)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            OperationalCapabilityOrchestrator, "_attempt", _spy
        )
        attempt = pydantic_ai_engine.attempt("resumo dos indicadores")
    assert calls == [], "pydantic_ai delegated to Application _attempt"
    assert attempt.status is GovernedCapabilityStatus.SUCCESS


def test_pydantic_ai_uses_shared_governed_primitives():
    import inspect as _inspect
    import app.infrastructure.orchestration.pydantic_ai_investigation as mod

    src = _inspect.getsource(mod)
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
            f"investigation runtime duplicates gate: {forbidden}"
        )


def test_engine_selection_is_config_gated_not_request_driven():
    import inspect

    from app.composition.root_composer import (
        _resolve_orchestration_attempt,
        _SUPPORTED_ORCHESTRATION_ENGINES,
    )

    assert _SUPPORTED_ORCHESTRATION_ENGINES == frozenset(
        {"pydantic_ai", "delia"}
    )
    assert list(
        inspect.signature(_resolve_orchestration_attempt).parameters
    ) == [
        "engine_name",
        "gates",
        "investigation_model",
        "investigation_model_factory",
        "subobjective_fanout_enabled",
        "checkpoint_db_path",
    ]


def test_langgraph_absent_from_production_requirements():
    from pathlib import Path

    req = (
        Path(__file__).resolve().parent.parent / "requirements.txt"
    ).read_text().lower()
    pins = "\n".join(
        line
        for line in req.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )
    assert "langgraph" not in pins
    assert "langchain" not in pins
    assert "pydantic-ai" in pins


# --- doc-192 scenario matrix (S2, S3, S4, S6, S7) ---------------------
# Provider-level fixtures from test_goal_evidence_relevance enable the
# goal/evidence judgment and recovery stages the FakePort harness
# cannot express. All boundary-only assertions.


from app.application.capability_provision.orchestration import (
    GOAL_EVIDENCE_RELEVANCE_INSTRUCTION_ID,
    GOAL_INSTRUCTION_ID,
    LIMITATION_GOAL_MISMATCH,
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
    # unqualified records answer. Any governed insufficiency caveat
    # counts: generic insufficient_evidence OR the non-blocking
    # goal_mismatch judgment (ad5424e75a) that annotates irrelevant
    # evidence without suppressing it.
    assert (
        attempt.status is not GovernedCapabilityStatus.SUCCESS
        or LIMITATION_INSUFFICIENT_EVIDENCE in attempt.limitations
        or LIMITATION_GOAL_MISMATCH in attempt.limitations
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
