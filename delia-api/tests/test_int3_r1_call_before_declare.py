"""INT-3 R1 — CALL_BEFORE_DECLARE governed pre-invocation gate.

Task DELIA-C3-T2-INT3-R1-PREINVOKE-GOVERNED-GATE-IMPLEMENTATION-01.

Real-model evidence (evals ``or-qwen14b-205331140f0e`` arm A /
``or-qwen14b-b37c420b89c3`` arm B, qwen/qwen3-14b): every scenario that
executed a business READ ran the FIRST owner call while
``InvestigationDeps.investigation_plan is None`` — the observation was
projected with ``coverage_note`` "Typed objective undeclared", so typed
obligation coverage could not be evaluated mid-flight.

Frozen-corpus A/B proved instruction specialization alone does not fix
the order (``GOAL_BEFORE_READ=0/4`` in both arms): the divergence is
structural — ``_governed_invoke`` executed the governed owner call with
no typed-plan precondition. The bounded Alternative-C remediation adds
a pre-invocation gate: a plan-dependent owner call (any operation
class other than the owner-published DISCOVERY class) while
``investigation_plan is None`` raises ``ModelRetry`` so the model
declares the goal via ``declare_investigation_goal`` and reissues the
call through the same governed path — no fabricated plan, no cached
invocation, no new authority.
"""

from __future__ import annotations

import json

from app.application.capability_provision.governed_capability_orchestrator import (
    OperationalCapabilityOrchestrator,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityAttempt,
    GovernedCapabilityProvenance,
    GovernedCapabilityStatus,
)
from app.application.interaction.turn_budget import TurnDeadline
from app.application.model_invocation.invoke_model import InvokeModel
from app.domain.evidence.model import SourceRef
from app.domain.specialist_interop.model import (
    InteropProtocol,
    SpecialistOperationClass,
    SpecialistOutcome,
    SpecialistResultProvenance,
    SpecialistResultStatus,
)
from app.infrastructure.orchestration import pydantic_ai_investigation as _inv
from app.infrastructure.orchestration.pydantic_ai_investigation import (
    PydanticAiInvestigationOrchestrator,
)
from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    RetryPromptPart,
    ToolCallPart,
    ToolReturnPart,
)
from pydantic_ai.models.function import FunctionModel
from tests.support.capability_fixtures import (
    FakeProvider,
    FakeProposalModel,
    _cap,
    _group,
    _providers,
    load_test_orchestration_instructions,
)
from tests.support.native_mcp_fixtures import (
    alpha_beta_servers,
    native_toolset_stub,
)


def _gates(providers=None) -> OperationalCapabilityOrchestrator:
    return OperationalCapabilityOrchestrator(
        providers or _providers(),
        orchestration_instructions=load_test_orchestration_instructions(),
        invoke_model=InvokeModel(FakeProposalModel(())),
    )


def _successful_owner_read() -> GovernedCapabilityAttempt:
    """Successful business READ exactly as a governed owner call lands
    in ``ctx.deps.collected`` — the trace-reproduced pre-declare call."""
    structured = {
        "capability": "search_processes",
        "action_id": "search_processes",
        "entity": "process",
        "shape": "paged_list",
        "data": {
            "items": [{"code": "P-001"}],
            "total": 1,
            "is_complete": True,
            "truncated": False,
        },
    }
    outcome = SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        content_text="records",
        structured=structured,
        provenance=SpecialistResultProvenance(
            specialist_id="teo",
            remote_name="read",
            protocol=InteropProtocol.MCP,
            correlation_id="r1",
            observed_at="2026-01-01T00:00:00Z",
        ),
        is_complete=True,
    )
    return GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SUCCESS,
        correlation_id="r1",
        content="records",
        limitations=(),
        provenance=GovernedCapabilityProvenance(
            source_refs=(
                SourceRef(
                    source_id="src",
                    source_system="teo",
                    provider_name="teo",
                    observed_at="2026-01-01T00:00:00Z",
                ),
            ),
            specialist_id="teo",
            remote_capability="read",
            action_id="read",
            protocol=InteropProtocol.MCP.value,
            observed_at="2026-01-01T00:00:00Z",
            correlation_id="r1",
            is_complete=True,
            operation_class="READ",
            invocation_vocabulary=("search_processes",),
            invocation_identity=(),
            invocation_scope=(),
        ),
        outcome=outcome,
    )


def _final_answer() -> ModelResponse:
    return ModelResponse(
        parts=[
            ToolCallPart(
                "final_result",
                {
                    "schema_version": "1",
                    "status": "insufficient",
                    "answer": "done",
                    "evidence_refs": [],
                    "unmet_obligations": [],
                    "limitations": [],
                },
            )
        ]
    )


def _valid_goal_call() -> ToolCallPart:
    return ToolCallPart(
        "declare_investigation_goal",
        {
            "goal_class": "read",
            "expected_delivery": "enumeration",
            "evidence_needed": [
                {
                    "description": "listagem de itens",
                    "evidence_source": "search_items",
                    "operation": "read",
                }
            ],
        },
    )


def _read_call() -> ToolCallPart:
    return ToolCallPart(
        "alpha.search_items", {"arguments": {"query": "processos"}}
    )


# -------------------------------------------------------------------
# Projection-level contract (defect context)
# -------------------------------------------------------------------


def test_dependent_owner_read_with_plan_none_yields_no_coverage():
    """A successful owner READ projected while ``investigation_plan``
    is None can only surface the pending-goal signal — the defect
    state the gate now prevents from ever being produced."""
    projection = _inv._attempt_projection(
        _successful_owner_read(),
        observation_index=0,
        plan=None,
        operation_class="READ",
        capability_id="teo.read",
    )
    assert projection["goal_declaration_pending"] is True
    note = (projection.get("coverage_note") or "").casefold()
    assert "typed objective undeclared" in note
    assert "coverage cannot be evaluated" in note


def test_same_read_with_accepted_plan_enables_midflight_coverage():
    """Control: the identical owner READ projected WITH an accepted
    typed plan carries evaluable coverage context — the only variable
    is plan presence."""
    plan = _gates()._accept_semantic_investigation_plan(
        goal_class="read",
        comparison_requested=False,
        target_identities=[],
        evidence_needed=[
            {
                "description": "listagem de processos",
                "evidence_source": "process",
                "operation": "read",
            }
        ],
        expected_delivery="enumeration",
        correlation="r1",
    )
    assert plan is not None
    projection = _inv._attempt_projection(
        _successful_owner_read(),
        observation_index=0,
        plan=plan,
        operation_class="READ",
        capability_id="teo.read",
    )
    assert "goal_declaration_pending" not in projection
    note = (projection.get("coverage_note") or "").casefold()
    assert "undeclared" not in note


# -------------------------------------------------------------------
# Behavioral boundary tests — the governed pre-invocation gate
# -------------------------------------------------------------------


def test_gate_blocks_dependent_read_then_recovers_via_declare():
    """R1-G01..G07: a dependent READ while ``investigation_plan`` is
    None never reaches the owner (spy count stays 0), the model
    receives the ModelRetry feedback, declares a valid goal, reissues
    the call through the same governed path and the executed
    observation carries evaluated (not 'undeclared') coverage."""
    gates = _gates()
    catalog = gates._project_semantic_tool_catalog(
        correlation="r1-g", deadline=TurnDeadline.start(30.0)
    )
    read_id = next(
        e["capability_id"]
        for e in catalog
        if e.get("operation_class") == "READ"
    )
    owner_calls: list[str] = []
    original = gates._governed_semantic_tool_invoke

    def _spy(**kwargs):
        owner_calls.append(str(kwargs.get("capability_id") or ""))
        return original(**kwargs)

    gates._governed_semantic_tool_invoke = _spy  # type: ignore[method-assign]
    saw_retry = {"v": False}

    def _fn(messages, _info):
        for m in messages:
            if isinstance(m, ModelRequest):
                for part in m.parts:
                    if isinstance(part, RetryPromptPart):
                        saw_retry["v"] = True
        prior = sum(1 for m in messages if isinstance(m, ModelResponse))
        if prior == 0:
            return ModelResponse(parts=[_read_call()])
        if prior == 1:
            return ModelResponse(parts=[_valid_goal_call()])
        if prior == 2:
            return ModelResponse(parts=[_read_call()])
        return _final_answer()

    engine = PydanticAiInvestigationOrchestrator(
        gates, model=FunctionModel(_fn), tool_calls_limit=8
    )
    with native_toolset_stub(alpha_beta_servers()):
        engine.attempt("quais itens existem")
    assert saw_retry["v"] is True
    assert owner_calls == [read_id]


def test_gate_keeps_owner_unreached_when_declaration_invalid():
    """R1-G04: a rejected declaration (dotted-proxy anchor) leaves the
    plan unset, so the reissued READ is gated AGAIN — owner invocation
    count remains 0 until a correct declaration is accepted."""
    gates = _gates()
    owner_calls: list[str] = []
    original = gates._governed_semantic_tool_invoke

    def _spy(**kwargs):
        owner_calls.append(str(kwargs.get("capability_id") or ""))
        return original(**kwargs)

    gates._governed_semantic_tool_invoke = _spy  # type: ignore[method-assign]
    invalid_return = {"v": False}

    def _fn(messages, _info):
        for m in messages:
            if isinstance(m, ModelRequest):
                for part in m.parts:
                    if (
                        isinstance(part, ToolReturnPart)
                        and part.tool_name == "declare_investigation_goal"
                        and "INVALID_GOAL" in str(part.content)
                    ):
                        invalid_return["v"] = True
        prior = sum(1 for m in messages if isinstance(m, ModelResponse))
        if prior == 0:
            return ModelResponse(parts=[_read_call()])
        if prior == 1:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        "declare_investigation_goal",
                        {
                            "goal_class": "read",
                            "expected_delivery": "enumeration",
                            "evidence_needed": [
                                {
                                    "description": "itens",
                                    "evidence_source": "alpha.search_items",
                                    "operation": "read",
                                }
                            ],
                        },
                    )
                ]
            )
        if prior == 2:
            return ModelResponse(parts=[_read_call()])
        if prior == 3:
            return ModelResponse(parts=[_valid_goal_call()])
        if prior == 4:
            return ModelResponse(parts=[_read_call()])
        return _final_answer()

    engine = PydanticAiInvestigationOrchestrator(
        gates, model=FunctionModel(_fn), tool_calls_limit=10,
        agent_retries=4,
    )
    with native_toolset_stub(alpha_beta_servers()):
        engine.attempt("quais itens existem")
    assert invalid_return["v"] is True
    assert owner_calls == ["alpha.search_items"]


def test_gate_exempts_owner_discovery_class_calls():
    """R1-G08: an owner-published DISCOVERY-class call executes without
    a typed plan — legitimate discovery that identifies capabilities
    must not be blocked by the gate."""
    discovery_cap = _cap(
        "alpha", "mcp", "search_items",
        op_class=SpecialistOperationClass.DISCOVERY,
    )
    providers = [
        FakeProvider(
            "pa",
            [_group("pa", "alpha", [discovery_cap])],
            outcomes={("alpha", "search_items"): []},
        )
    ]
    gates = _gates(providers)
    owner_calls: list[str] = []
    original = gates._governed_semantic_tool_invoke

    def _spy(**kwargs):
        owner_calls.append(str(kwargs.get("capability_id") or ""))
        return original(**kwargs)

    gates._governed_semantic_tool_invoke = _spy  # type: ignore[method-assign]

    def _fn(messages, _info):
        prior = sum(1 for m in messages if isinstance(m, ModelResponse))
        if prior == 0:
            return ModelResponse(parts=[_read_call()])
        return _final_answer()

    engine = PydanticAiInvestigationOrchestrator(
        gates, model=FunctionModel(_fn), tool_calls_limit=4
    )
    with native_toolset_stub(alpha_beta_servers()):
        engine.attempt("descubra o catálogo")
    assert owner_calls == ["alpha.search_items"]


def test_gate_is_provider_and_name_agnostic():
    """R1-G15: classification comes from the owner-published
    ``operation_class`` contract — a READ-class capability on the
    OTHER provider/group is gated identically."""
    gates = _gates()
    owner_calls: list[str] = []
    original = gates._governed_semantic_tool_invoke

    def _spy(**kwargs):
        owner_calls.append(str(kwargs.get("capability_id") or ""))
        return original(**kwargs)

    gates._governed_semantic_tool_invoke = _spy  # type: ignore[method-assign]

    def _fn(messages, _info):
        prior = sum(1 for m in messages if isinstance(m, ModelResponse))
        if prior == 0:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        "beta.read_guidance",
                        {"arguments": {"query": "guia"}},
                    )
                ]
            )
        return _final_answer()

    engine = PydanticAiInvestigationOrchestrator(
        gates, model=FunctionModel(_fn), tool_calls_limit=4
    )
    with native_toolset_stub(alpha_beta_servers()):
        engine.attempt("consulte a orientação")
    assert owner_calls == []


def test_clarification_tool_remains_reachable_without_plan():
    """R1-G09: ``request_user_clarification`` is a FunctionToolset
    channel, not a governed owner call — the gate must not affect it."""
    gates = _gates()
    owner_calls: list[str] = []
    original = gates._governed_semantic_tool_invoke

    def _spy(**kwargs):
        owner_calls.append(str(kwargs.get("capability_id") or ""))
        return original(**kwargs)

    gates._governed_semantic_tool_invoke = _spy  # type: ignore[method-assign]

    def _fn(messages, _info):
        prior = sum(1 for m in messages if isinstance(m, ModelResponse))
        if prior == 0:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        "request_user_clarification",
                        {"question": "qual código do produto?"},
                    )
                ]
            )
        return _final_answer()

    engine = PydanticAiInvestigationOrchestrator(
        gates, model=FunctionModel(_fn), tool_calls_limit=4
    )
    with native_toolset_stub(alpha_beta_servers()):
        engine.attempt("preciso da estrutura")
    assert owner_calls == []


# -------------------------------------------------------------------
# Goal-declaration reliability (INT3-GOAL-DECLARATION-RELIABILITY)
#
# Real-eval or-qwen14b-fe85fee80a30: the model already held the owner
# vocabulary (required_args entity=process/action=search) but anchored
# obligations to the visible surface name ("teo.read") or broke
# `operation` with an action token while fixing the anchor — the
# rejection named the vocab SETS, never the offending field/value or
# the legitimate tokens the model itself had declared.
# -------------------------------------------------------------------


def _declare_call(**overrides) -> ToolCallPart:
    payload: dict = {
        "goal_class": "read",
        "expected_delivery": "enumeration",
        "evidence_needed": [
            {
                "description": "listagem de processos",
                "evidence_source": "alpha.search_items",
                "operation": "read",
                "required_args": {
                    "entity": "process",
                    "action": "search",
                },
            }
        ],
    }
    payload.update(overrides)
    return ToolCallPart("declare_investigation_goal", payload)


def _declare_returns(messages) -> list[dict]:
    out = []
    for m in messages:
        if not isinstance(m, ModelRequest):
            continue
        for part in m.parts:
            if (
                isinstance(part, ToolReturnPart)
                and part.tool_name == "declare_investigation_goal"
                and isinstance(part.content, str)
            ):
                out.append(json.loads(part.content))
    return out


def _collect_declare_returns(messages, store: list[dict]) -> None:
    """Append only declare returns not yet recorded — the same
    ToolReturnPart is visible in every subsequent message history."""
    fresh = _declare_returns(messages)
    store.extend(fresh[len(store) :])


def test_rejection_echoes_field_diagnosis_and_anchor_candidates():
    """G01/G04: a dotted-anchor rejection names the rejected surface
    token AND echoes the owner-vocabulary selector values the model
    itself declared in required_args — bounded correction feedback,
    never an anchor catalog. The corrected declaration is accepted and
    the reissued READ reaches the governed path exactly once."""
    gates = _gates()
    owner_calls: list[str] = []
    original = gates._governed_semantic_tool_invoke

    def _spy(**kwargs):
        owner_calls.append(str(kwargs.get("capability_id") or ""))
        return original(**kwargs)

    gates._governed_semantic_tool_invoke = _spy  # type: ignore[method-assign]
    returns: list[dict] = []

    def _fn(messages, _info):
        _collect_declare_returns(messages, returns)
        prior = sum(1 for m in messages if isinstance(m, ModelResponse))
        if prior == 0:
            return ModelResponse(parts=[_declare_call()])
        if prior == 1:
            return ModelResponse(
                parts=[
                    _declare_call(
                        evidence_needed=[
                            {
                                "description": "listagem de processos",
                                "evidence_source": "process",
                                "operation": "read",
                                "required_args": {
                                    "entity": "process",
                                    "action": "search",
                                },
                            }
                        ]
                    )
                ]
            )
        if prior == 2:
            return ModelResponse(parts=[_read_call()])
        return _final_answer()

    engine = PydanticAiInvestigationOrchestrator(
        gates, model=FunctionModel(_fn), tool_calls_limit=8
    )
    with native_toolset_stub(alpha_beta_servers()):
        engine.attempt("quais processos existem")
    rejections = [r for r in returns if r.get("status") == "INVALID_GOAL"]
    assert len(rejections) == 1
    first = rejections[0]
    assert "alpha.search_items" in (first.get("rejected_anchors") or [])
    assert "process" in (first.get("anchor_candidates") or [])
    assert "search" in (first.get("anchor_candidates") or [])
    # The corrected declaration was accepted and the dependent READ
    # ran once through the governed path.
    assert owner_calls == ["alpha.search_items"]


def test_rejection_names_invalid_operation_class():
    """Trace-reproduced failure (scenario A, decl1): the model fixed
    the anchor to a correct owner token but set `operation` to the
    action token "search" — rejected as an invalid operation class.
    The feedback must name the offending value so the next proposal
    fixes the actual divergence."""
    gates = _gates()
    returns: list[dict] = []

    def _fn(messages, _info):
        _collect_declare_returns(messages, returns)
        prior = sum(1 for m in messages if isinstance(m, ModelResponse))
        if prior == 0:
            return ModelResponse(
                parts=[
                    _declare_call(
                        evidence_needed=[
                            {
                                "description": "listagem",
                                "evidence_source": "process",
                                "operation": "search",
                                "required_args": {
                                    "entity": "process",
                                    "action": "search",
                                },
                            }
                        ]
                    )
                ]
            )
        if prior == 1:
            return ModelResponse(
                parts=[
                    _declare_call(
                        evidence_needed=[
                            {
                                "description": "listagem",
                                "evidence_source": "process",
                                "required_args": {"entity": "process"},
                            }
                        ]
                    )
                ]
            )
        return _final_answer()

    engine = PydanticAiInvestigationOrchestrator(
        gates, model=FunctionModel(_fn), tool_calls_limit=6
    )
    with native_toolset_stub(alpha_beta_servers()):
        engine.attempt("quais processos existem")
    rejections = [r for r in returns if r.get("status") == "INVALID_GOAL"]
    assert len(rejections) == 1
    assert rejections[0].get("invalid_operations") == ["search"]
    assert "operation" in (rejections[0].get("operation_guidance") or "")
    assert "process" in (rejections[0].get("anchor_candidates") or [])


def test_anchor_candidates_never_fabricate_vocabulary():
    """Guard: candidates come ONLY from selector values the model
    itself declared — non-selector args and dotted values are never
    echoed; a rejection without declared selectors carries no
    fabricated vocabulary."""
    gates = _gates()
    returns: list[dict] = []

    def _fn(messages, _info):
        _collect_declare_returns(messages, returns)
        prior = sum(1 for m in messages if isinstance(m, ModelResponse))
        if prior == 0:
            return ModelResponse(
                parts=[
                    _declare_call(
                        evidence_needed=[
                            {
                                "description": "listagem",
                                "evidence_source": "alpha.search_items",
                                "operation": "read",
                                "required_args": {
                                    "entity": "teo.read",
                                    "params": {"q": "process"},
                                },
                            }
                        ]
                    )
                ]
            )
        return _final_answer()

    engine = PydanticAiInvestigationOrchestrator(
        gates, model=FunctionModel(_fn), tool_calls_limit=4
    )
    with native_toolset_stub(alpha_beta_servers()):
        engine.attempt("quais processos existem")
    rejections = [r for r in returns if r.get("status") == "INVALID_GOAL"]
    assert len(rejections) == 1
    first = rejections[0]
    # "teo.read" is dotted → excluded; "q"/"params" are not selector
    # keys → nothing fabricated.
    assert not first.get("anchor_candidates")
    assert "alpha.search_items" in (first.get("rejected_anchors") or [])
