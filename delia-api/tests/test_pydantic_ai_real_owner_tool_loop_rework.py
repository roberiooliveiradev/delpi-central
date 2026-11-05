"""Doc 237 — real owner tool loop + evidence E1–E4 RED/GREEN."""

from __future__ import annotations

from app.application.capability_provision.orchestration import (
    OBLIGATION_SATISFIED,
    OBLIGATION_UNSATISFIED,
    SemanticInvestigationPlan,
    _attempt_satisfies_obligation,
    _authoritative_structure_root,
    _bind_identifier_args_from_utterance,
    _bind_missing_required_query,
    _evaluate_material_obligations,
    _finalize_agent_collected_attempts,
    _is_business_evidence_attempt,
    _listing_failure_is_transient,
)
from app.domain.specialist_interop.model import SpecialistOperationClass
from tests.support.capability_fixtures import FakeProvider, _cap, _group, _outcome
from app.application.interaction.capability_attempt import (
    OWNER_PATH_UNBOUND,
    GovernedCapabilityAttempt,
    GovernedCapabilityStatus,
)
from app.application.interaction.contracts import (
    VerifiedCompositeEvidence,
)
from app.application.interaction.turn_budget import TurnDeadline
from app.domain.evidence.model import SourceRef
from app.infrastructure.orchestration.pydantic_ai_investigation import (
    PydanticAiInvestigationOrchestrator,
    focus_arguments_on_next_identifier,
    uncovered_user_identifiers,
)
from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import FunctionModel
from tests.support.native_mcp_fixtures import (
    alpha_beta_servers,
    native_toolset_stub,
)
from tests.test_pydantic_ai_semantic_rework import (
    _gates,
    _success_attempt,
)

import pytest


@pytest.fixture(autouse=True)
def _native_toolsets_stub():
    with native_toolset_stub(alpha_beta_servers()):
        yield


def _final_answer(answer: str = "", status: str = "insufficient",
                  refs: list | None = None) -> ModelResponse:
    """Native typed output — the Agent now ends every run with a
    ``final_result`` call carrying the strict InvestigationAnswer
    shape instead of free text."""
    return ModelResponse(
        parts=[
            ToolCallPart(
                "final_result",
                {
                    "schema_version": "1",
                    "status": status,
                    "answer": answer,
                    "evidence_refs": refs or [],
                    "unmet_obligations": [],
                    "limitations": [],
                },
            )
        ]
    )



def test_e2_capability_name_does_not_satisfy_obligation():
    attempt = _success_attempt(
        content="search hit",
        root="OTHER",
        structured={
            "items": [{"code": "OTHER", "label": "x", "path": ["OTHER"]}]
        },
    )
    assert not _attempt_satisfies_obligation(attempt, "search_items")
    assert _attempt_satisfies_obligation(attempt, "OTHER")


def test_e2_child_under_wrong_root_does_not_satisfy():
    attempt = _success_attempt(
        content="mentions product",
        root="PARENT99",
        structured={
            "items": [
                {
                    "code": "PARENT99",
                    "components": [
                        {"code": "90260147", "label": "child"}
                    ],
                }
            ]
        },
    )
    assert not _attempt_satisfies_obligation(attempt, "90260147")
    assert _attempt_satisfies_obligation(attempt, "PARENT99")


def test_e1_composition_does_not_hide_missing_obligation_c():
    gates = _gates()
    plan = gates._accept_semantic_investigation_plan(
        goal_class="compare",
        comparison_requested=True,
        target_identities=["A1", "B2"],
        evidence_needed=["A1", "B2", "SPEC-C"],
        correlation="c1",
    )
    assert plan is not None
    composed = GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SUCCESS,
        correlation_id="c1",
        content="A vs B",
        verified_composition=VerifiedCompositeEvidence(
            source_roots=("A1", "B2"),
            source_lineage=(
                (
                    SourceRef(
                        source_id="A1",
                        source_system="pa",
                        provider_name="pa",
                        observed_at="2026-01-01T00:00:00Z",
                    ),
                ),
                (
                    SourceRef(
                        source_id="B2",
                        source_system="pa",
                        provider_name="pa",
                        observed_at="2026-01-01T00:00:00Z",
                    ),
                ),
            ),
            observed_at="2026-01-01T00:00:00Z",
            correlation_id="c1",
            verdict="differences_found",
        ),
    )
    a = _success_attempt(content="a", root="A1")
    b = _success_attempt(content="b", root="B2")
    result = _finalize_agent_collected_attempts(
        gates,
        input_text="compare A and B and include SPEC-C",
        collected=(a, b),
        correlation="c1",
        workspace_context=None,
        deadline=TurnDeadline.start(30.0),
        unbound_outcome=OWNER_PATH_UNBOUND,
        plan=plan,
        composed_attempt=composed,
    )
    assert result.status is GovernedCapabilityStatus.NOT_APPLICABLE
    assert "composition_does_not_satisfy_goal" in result.limitations
    assert any("SPEC-C" in lim for lim in result.limitations)


def test_e3_plan_omission_of_declared_obligation_blocks_success():
    gates = _gates()
    plan = gates._accept_semantic_investigation_plan(
        goal_class="read",
        comparison_requested=False,
        target_identities=["P1"],
        evidence_needed=["P1", "EXTRA-REQ"],
        correlation="c1",
    )
    only = _success_attempt(content="p1", root="P1")
    result = _finalize_agent_collected_attempts(
        gates,
        input_text="P1 with EXTRA-REQ",
        collected=(only,),
        correlation="c1",
        workspace_context=None,
        deadline=TurnDeadline.start(30.0),
        unbound_outcome=None,
        plan=plan,
    )
    assert result.status is GovernedCapabilityStatus.NOT_APPLICABLE
    assert any("EXTRA-REQ" in lim for lim in result.limitations)


def test_e4_multiple_observations_preserve_both_contents():
    gates = _gates()
    a = _success_attempt(content="fact-alpha-body", root="FA")
    b = _success_attempt(content="fact-beta-body", root="FB")
    result = _finalize_agent_collected_attempts(
        gates,
        input_text="two independent facts",
        collected=(a, b),
        correlation="c1",
        workspace_context=None,
        deadline=TurnDeadline.start(30.0),
        unbound_outcome=None,
        plan=None,
    )
    assert result.status is GovernedCapabilityStatus.SUCCESS
    assert result.verified_composition is None
    assert "fact-alpha-body" in (result.content or "")
    assert "fact-beta-body" in (result.content or "")
    assert "multiple_observations_without_compose" in result.limitations


def test_dynamic_owner_tool_invokes_governed_path():
    gates = _gates()
    catalog = gates._project_semantic_tool_catalog(
        correlation="c", deadline=TurnDeadline.start(30.0)
    )
    assert catalog, "test providers must expose READ catalog"
    cap = catalog[0]
    tool_name = cap["capability_id"]
    calls: list[str] = []
    original = gates._governed_semantic_tool_invoke

    def _spy(**kwargs):
        calls.append(str(kwargs.get("capability_id") or ""))
        return original(**kwargs)

    gates._governed_semantic_tool_invoke = _spy  # type: ignore[method-assign]

    def _fn(messages, _info):
        if not any(isinstance(m, ModelResponse) for m in messages):
            return ModelResponse(
                parts=[
                    ToolCallPart(tool_name, {"arguments": {}})
                ]
            )
        return _final_answer("done")

    engine = PydanticAiInvestigationOrchestrator(
        gates, model=FunctionModel(_fn), tool_calls_limit=4
    )
    with native_toolset_stub(alpha_beta_servers()):
        engine.attempt("read something")
    assert calls and calls[0] == cap["capability_id"]


def test_empty_owner_result_is_not_business_evidence():
    attempt = _success_attempt(
        content="Nenhum resultado encontrado.",
        root="90260147",
    )
    assert not _is_business_evidence_attempt(attempt)


def test_usage_limit_finalizes_collected_evidence():
    gates = _gates()
    catalog = gates._project_semantic_tool_catalog(
        correlation="c", deadline=TurnDeadline.start(30.0)
    )
    tool_name = catalog[0]["capability_id"]
    original = gates._governed_semantic_tool_invoke

    def _spy(**kwargs):
        return _success_attempt(content="estrutura A", root="90260147")

    gates._governed_semantic_tool_invoke = _spy  # type: ignore[method-assign]
    steps = {"n": 0}

    def _fn(messages, _info):
        steps["n"] += 1
        return ModelResponse(
            parts=[ToolCallPart(tool_name, {"arguments": {}})]
        )

    engine = PydanticAiInvestigationOrchestrator(
        gates, model=FunctionModel(_fn), tool_calls_limit=1
    )
    with native_toolset_stub(alpha_beta_servers()):
        attempt = engine.attempt("estrutura 90260147")
    assert attempt.error_code != "investigation_agent_error"
    assert "tool_calls_limit_reached" in attempt.limitations
    assert original is not None


def test_focus_query_targets_next_uncovered_identifier():
    covered = _success_attempt(content="estrutura A", root="90260147")
    first = focus_arguments_on_next_identifier(
        {"query": "Compare 90260147 e 90260148"},
        input_text="Compare 90260147 e 90260148",
        collected=[],
    )
    assert "90260147" in first["query"]
    assert "90260148" not in first["query"]
    assert "Compare" in first["query"]
    second = focus_arguments_on_next_identifier(
        {"query": "Compare 90260147 e 90260148"},
        input_text="Compare 90260147 e 90260148",
        collected=[covered],
    )
    assert "90260148" in second["query"]
    assert "90260147" not in second["query"]
    kept = focus_arguments_on_next_identifier(
        {"query": "90260148"},
        input_text="Compare 90260147 e 90260148",
        collected=[covered],
    )
    assert kept["query"] == "90260148"
    repeated = focus_arguments_on_next_identifier(
        {"query": "estrutura do produto 90260147"},
        input_text="Compare 90260147 e 90260148",
        collected=[covered],
    )
    assert "90260148" in repeated["query"]
    assert "90260147" not in repeated["query"]
    assert "estrutura" in repeated["query"]


def test_uncovered_identifiers_ignore_observed_root():
    covered = _success_attempt(content="estrutura", root="90260147")
    pending = uncovered_user_identifiers(
        "Compare 90260147 e 90260148",
        [covered],
    )
    assert pending == ["90260148"]
    assert (
        uncovered_user_identifiers(
            "Compare 90260147 e 90260148",
            [
                covered,
                _success_attempt(content="b", root="90260148"),
            ],
        )
        == []
    )


def test_premature_clarification_is_rejected_when_identifiers_remain():
    gates = _gates()
    calls: list[str] = []
    original = gates._governed_semantic_tool_invoke

    def _spy(**kwargs):
        calls.append(str(kwargs.get("capability_id") or ""))
        return _success_attempt(content="estrutura A", root="90260147")

    gates._governed_semantic_tool_invoke = _spy  # type: ignore[method-assign]
    catalog = gates._project_semantic_tool_catalog(
        correlation="c", deadline=TurnDeadline.start(30.0)
    )
    tool_name = catalog[0]["capability_id"]
    steps = {"n": 0}

    def _fn(messages, _info):
        steps["n"] += 1
        if steps["n"] == 1:
            return ModelResponse(
                parts=[ToolCallPart(tool_name, {"arguments": {}})]
            )
        if steps["n"] == 2:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        "request_user_clarification",
                        {
                            "question": "Qual o segundo produto?",
                            "missing_aspects": ["90260148"],
                        },
                    )
                ]
            )
        if steps["n"] == 3:
            return ModelResponse(
                parts=[ToolCallPart(tool_name, {"arguments": {}})]
            )
        return _final_answer("done")

    engine = PydanticAiInvestigationOrchestrator(
        gates, model=FunctionModel(_fn), tool_calls_limit=6
    )
    with native_toolset_stub(alpha_beta_servers()):
        attempt = engine.attempt("Compare 90260147 e 90260148")
    assert attempt.status is not GovernedCapabilityStatus.CLARIFICATION_REQUIRED
    assert len(calls) >= 2


def test_model_factory_builds_a_client_per_attempt():
    gates = _gates()
    built: list[int] = []

    def _factory():
        built.append(1)

        def _fn(messages, _info):
            if not any(isinstance(m, ModelResponse) for m in messages):
                return _final_answer("ok")
            return _final_answer("ok")

        return FunctionModel(_fn)

    engine = PydanticAiInvestigationOrchestrator(
        gates, model_factory=_factory, tool_calls_limit=2
    )
    engine.attempt("estrutura 11111")
    engine.attempt("estrutura 22222")
    assert len(built) == 2


def test_list_only_does_not_fabricate_business_success():
    gates = _gates()

    def _fn(messages, _info):
        if not any(isinstance(m, ModelResponse) for m in messages):
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        "declare_investigation_goal",
                        {"goal_class": "read"},
                    )
                ]
            )
        return _final_answer("I listed tools")

    engine = PydanticAiInvestigationOrchestrator(
        gates, model=FunctionModel(_fn), tool_calls_limit=4
    )
    attempt = engine.attempt("estrutura 90260147")
    assert attempt.status is GovernedCapabilityStatus.NOT_APPLICABLE
    assert attempt.error_code == "investigation_no_tool_observations"


def test_bind_missing_required_query_from_utterance():
    schema = {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    }
    bound = _bind_missing_required_query(
        {},
        input_schema=schema,
        input_text="Qual a estrutura do produto 90260147?",
    )
    assert bound["query"].startswith("Qual a estrutura")
    kept = _bind_missing_required_query(
        {"query": "keep-me"},
        input_schema=schema,
        input_text="other",
    )
    assert kept["query"] == "keep-me"


def test_bind_identifier_args_from_utterance_single_code():
    schema = {
        "type": "object",
        "properties": {
            "code": {"type": "string"},
            "page": {"type": "integer", "default": 1},
        },
        "required": ["code"],
    }
    bound = _bind_identifier_args_from_utterance(
        schema, "Qual a estrutura do produto 90260147?"
    )
    assert bound == {"code": "90260147"}
    assert (
        _bind_identifier_args_from_utterance(schema, "sem codigo") is None
    )


def test_declared_data_root_is_authoritative():
    attempt = _success_attempt(
        content="child rows only in text",
        root="CHILD01",
        structured={
            "data": {
                "root": {"code": "90260147", "path": ["90260147"]},
                "items": [
                    {
                        "code": "CHILD01",
                        "label": "c",
                        "path": ["90260147", "CHILD01"],
                    }
                ],
            }
        },
    )
    assert _authoritative_structure_root(attempt) == "90260147"
    assert _attempt_satisfies_obligation(attempt, "90260147")


def test_discovery_chained_owner_read_counts_as_business_evidence():
    schema = {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    }
    discover = _cap(
        "alpha",
        "pa",
        "discover_items",
        schema=schema,
        op_class=SpecialistOperationClass.DISCOVERY,
    )
    provider = FakeProvider(
        "pa",
        [_group("pa", "alpha", [discover])],
        outcomes={},
    )
    gates = _gates(providers=[provider])

    def _chained(*_a, **_k):
        return (
            _outcome(
                "estrutura 90260147",
                structured={
                    "action_id": "get_product_structure",
                    "entity": "product_structure",
                    "data": {
                        "root": {"code": "90260147", "path": ["90260147"]},
                        "items": [
                            {
                                "code": "90260147",
                                "label": "PA",
                                "path": ["90260147"],
                            }
                        ],
                    },
                },
            ),
            "get_product_structure",
            "execute_items",
        )

    gates._invoke_selected = _chained  # type: ignore[method-assign]
    attempt = gates._governed_semantic_tool_invoke(
        capability_id=discover.capability_id,
        arguments={},
        input_text="Qual a estrutura do produto 90260147?",
        correlation="c-chain",
        actor_user_id="u1",
        session_id="s1",
        workspace_context=None,
        prior_turns=(),
        prepare_only=False,
        deadline=TurnDeadline.start(30.0),
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert "discovery_metadata_observation" not in attempt.limitations
    assert attempt.provenance is not None
    assert attempt.provenance.is_complete
    assert _is_business_evidence_attempt(attempt)
    assert _attempt_satisfies_obligation(attempt, "90260147")


def test_pure_discovery_envelope_still_tagged_metadata():
    schema = {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    }
    discover = _cap(
        "alpha",
        "pa",
        "discover_items",
        schema=schema,
        op_class=SpecialistOperationClass.DISCOVERY,
    )
    provider = FakeProvider(
        "pa",
        [_group("pa", "alpha", [discover])],
        outcomes={},
    )
    gates = _gates(providers=[provider])

    def _pure_discovery(*_a, **_k):
        return (
            _outcome(
                "candidates only",
                structured={
                    "candidates": [
                        {
                            "candidate_token": "tok-1",
                            "action_id": "get_product_structure",
                        }
                    ]
                },
            ),
            "discover_items",
            "discover_items",
        )

    gates._invoke_selected = _pure_discovery  # type: ignore[method-assign]
    attempt = gates._governed_semantic_tool_invoke(
        capability_id=discover.capability_id,
        arguments={"query": "estrutura 90260147"},
        input_text="estrutura 90260147",
        correlation="c-meta",
        actor_user_id="u1",
        session_id="s1",
        workspace_context=None,
        prior_turns=(),
        prepare_only=False,
        deadline=TurnDeadline.start(30.0),
    )
    assert "discovery_metadata_observation" in attempt.limitations
    assert not _is_business_evidence_attempt(attempt)


def test_listing_timeout_is_transient_and_denial_is_not():
    assert _listing_failure_is_transient("mcp_timeout")
    assert _listing_failure_is_transient("provider_unavailable")
    assert not _listing_failure_is_transient("authz_denied")


def test_knowledge_does_not_complete_uncovered_identifier():
    knowledge = _success_attempt(
        content="Seção do guia metodológico.",
        root="GUIDE",
        structured={"data": {"section": "s0001"}},
    )
    result = _finalize_agent_collected_attempts(
        _gates(),
        input_text="Qual a estrutura do produto 90260147 e o guia?",
        collected=(knowledge,),
        correlation="c-partial",
        workspace_context=None,
        deadline=TurnDeadline.start(30.0),
        unbound_outcome=OWNER_PATH_UNBOUND,
    )
    assert result.error_code == "investigation_partial_coverage"
    assert result.status is GovernedCapabilityStatus.NOT_APPLICABLE
    assert "guia" in (result.content or "").casefold() or "Seção" in (
        result.content or ""
    )
    assert "uncovered_identifier:90260147" in result.limitations


def test_consulted_miss_names_uncovered_identifiers():
    miss = GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.NOT_APPLICABLE,
        correlation_id="c-miss",
        content=None,
        limitations=("discovery_metadata_observation",),
        error_code="investigation_no_business_evidence",
    )
    result = _finalize_agent_collected_attempts(
        _gates(),
        input_text="Quais componentes diferem entre 90260147, 90260148 e 50220013?",
        collected=(miss,),
        correlation="c-miss",
        workspace_context=None,
        deadline=TurnDeadline.start(30.0),
        unbound_outcome=OWNER_PATH_UNBOUND,
    )
    assert result.error_code == "investigation_no_business_evidence"
    assert "identifier_coverage_incomplete" in result.limitations
    assert "uncovered_identifier:90260147" in result.limitations
    assert "uncovered_identifier:90260148" in result.limitations
    assert "uncovered_identifier:50220013" in result.limitations


def test_two_authoritative_roots_stay_complete():
    result = _finalize_agent_collected_attempts(
        _gates(),
        input_text="Compare 90260147 e 90260148",
        collected=(
            _success_attempt(content="estrutura A", root="90260147"),
            _success_attempt(content="estrutura B", root="90260148"),
        ),
        correlation="c-both",
        workspace_context=None,
        deadline=TurnDeadline.start(30.0),
        unbound_outcome=None,
    )
    assert result.status is GovernedCapabilityStatus.SUCCESS
    assert result.error_code != "investigation_partial_coverage"


def test_repeated_equivalent_failure_does_not_reinvoke_owner():
    gates = _gates()
    catalog = gates._project_semantic_tool_catalog(
        correlation="c", deadline=TurnDeadline.start(30.0)
    )
    tool_name = catalog[0]["capability_id"]
    calls: list[int] = []

    def _spy(**kwargs):
        calls.append(1)
        return GovernedCapabilityAttempt(
            status=GovernedCapabilityStatus.NOT_APPLICABLE,
            correlation_id="c",
            error_code="arguments_schema_rejected",
        )

    gates._governed_semantic_tool_invoke = _spy  # type: ignore[method-assign]
    steps = {"n": 0}

    def _fn(messages, _info):
        steps["n"] += 1
        if steps["n"] < 3:
            return ModelResponse(
                parts=[ToolCallPart(tool_name, {"arguments": {"query": "x"}})]
            )
        return _final_answer("stop")

    engine = PydanticAiInvestigationOrchestrator(
        gates, model=FunctionModel(_fn), tool_calls_limit=6
    )
    with native_toolset_stub(alpha_beta_servers()):
        engine.attempt("consulta 90260147")
    assert calls == [1]


def test_clarification_does_not_replace_collected_evidence():
    gates = _gates()
    catalog = gates._project_semantic_tool_catalog(
        correlation="c", deadline=TurnDeadline.start(30.0)
    )
    tool_name = catalog[0]["capability_id"]
    gates._governed_semantic_tool_invoke = (  # type: ignore[method-assign]
        lambda **kwargs: _success_attempt(
            content="estrutura A", root="90260147"
        )
    )
    steps = {"n": 0}

    def _fn(messages, _info):
        steps["n"] += 1
        if steps["n"] == 1:
            return ModelResponse(
                parts=[ToolCallPart(tool_name, {"arguments": {}})]
            )
        if steps["n"] == 2:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        "request_user_clarification",
                        {"question": "Confirma o produto?"},
                    )
                ]
            )
        return _final_answer("done")

    engine = PydanticAiInvestigationOrchestrator(
        gates, model=FunctionModel(_fn), tool_calls_limit=4
    )
    attempt = engine.attempt("estrutura 90260147")
    assert attempt.status is not GovernedCapabilityStatus.CLARIFICATION_REQUIRED
    assert attempt.status is GovernedCapabilityStatus.SUCCESS


def test_missing_identifier_without_evidence_asks_clarification():
    gates = _gates()

    def _fn(messages, _info):
        return _final_answer("não sei")

    engine = PydanticAiInvestigationOrchestrator(
        gates, model=FunctionModel(_fn), tool_calls_limit=4
    )
    attempt = engine.attempt("Me mostre a estrutura desse produto")
    assert attempt.status is GovernedCapabilityStatus.CLARIFICATION_REQUIRED
    assert "identificador" in (attempt.content or "").casefold()
