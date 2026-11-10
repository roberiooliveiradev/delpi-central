"""INT-1 final bounded rework — F1–F4 only.

Host-isolated deterministic suite. Extends the existing
``PydanticAiInvestigationOrchestrator``; no second Agent.
"""

from __future__ import annotations

import pytest
from tests.support.native_mcp_fixtures import (
    alpha_beta_servers,
    native_toolset_stub,
    owner_tool_server,
)


@pytest.fixture(autouse=True)
def _native_toolsets_stub():
    with native_toolset_stub(alpha_beta_servers()):
        yield


from app.application.capability_provision.semantic_capability_support import (
    INVESTIGATION_PROGRESS_NEW,
    INVESTIGATION_PROGRESS_RELATED,
    _finalize_agent_collected_attempts,
    classify_investigation_progress,
)
from app.application.interaction.capability_attempt import (
    OWNER_PATH_UNBOUND,
    GovernedCapabilityAttempt,
    GovernedCapabilityStatus,
)
from app.application.interaction.turn_budget import TurnDeadline
from app.application.specialist_interop.errors import OWNER_ARGUMENT_REJECTED
from app.infrastructure.orchestration.pydantic_ai_investigation import (
    PydanticAiInvestigationOrchestrator,
)
from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import FunctionModel
from tests.test_pydantic_ai_semantic_rework import (
    _gates,
    _providers,
    _read_plan,
    _success_attempt,
)
from tests.support.capability_fixtures import (
    FakeProvider,
    _group,
    _outcome,
)
from app.domain.specialist_interop.model import SpecialistOperationClass
from app.application.capability_provision.contracts import ProviderCapability


def _final_answer(answer: str = "done", status: str = "insufficient"):
    return ModelResponse(
        parts=[
            ToolCallPart(
                "final_result",
                {
                    "schema_version": "1",
                    "status": status,
                    "answer": answer,
                    "evidence_refs": [],
                    "unmet_obligations": [],
                    "limitations": [],
                },
            )
        ]
    )


# ---------------- F1: material arg change after rejection -------------


def test_f1_identical_rejection_short_circuits_but_new_args_invoke():
    gates = _gates()
    catalog = gates._project_semantic_tool_catalog(
        correlation="f1",
        deadline=TurnDeadline.start(30.0),
        actor_user_id="u1",
    )
    tool_name = catalog[0]["capability_id"]
    calls: list[dict] = []
    phase = {"n": 0}

    def _invoke(**kwargs):
        args = dict(kwargs.get("arguments") or {})
        calls.append(args)
        code = ""
        inner = args.get("arguments")
        if isinstance(inner, dict):
            code = str(inner.get("code") or "")
        elif "code" in args:
            code = str(args.get("code") or "")
        # Also accept query carrying the identifier after focus helper.
        query = str(args.get("query") or "")
        if code.strip() == "90260921" or "90260921" in query:
            return _success_attempt(
                content="BOM for 90260921",
                root="90260921",
            )
        return GovernedCapabilityAttempt(
            status=GovernedCapabilityStatus.SOURCE_UNAVAILABLE,
            correlation_id="f1",
            error_code=OWNER_ARGUMENT_REJECTED,
            owner_hint="arguments.code must be a non-empty string",
        )

    gates._governed_semantic_tool_invoke = _invoke  # type: ignore[method-assign]
    steps = {"n": 0}

    def _fn(messages, _info):
        steps["n"] += 1
        # Count model responses already present.
        prior = sum(1 for m in messages if isinstance(m, ModelResponse))
        if prior == 0:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        tool_name,
                        {"arguments": {"code": ""}},
                    )
                ]
            )
        if prior == 1:
            # After ModelRetry / observation, resubmit identical bad args
            # once — fingerprint short-circuit must not loop forever.
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        tool_name,
                        {"arguments": {"code": ""}},
                    )
                ]
            )
        if prior == 2:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        tool_name,
                        {"arguments": {"code": "90260921"}},
                    )
                ]
            )
        return _final_answer("estrutura observada", status="complete")

    engine = PydanticAiInvestigationOrchestrator(
        gates, model=FunctionModel(_fn), tool_calls_limit=6
    )
    result = engine.attempt("Qual é a estrutura do produto 90260921?")
    # Materially different corrected args must have reached the owner.
    assert any(
        (isinstance(c.get("arguments"), dict) and c["arguments"].get("code") == "90260921")
        or c.get("code") == "90260921"
        or "90260921" in str(c.get("query") or "")
        for c in calls
    ), calls
    # Identical empty rejection must not dominate call count unboundedly.
    empty_calls = [
        c
        for c in calls
        if (
            (isinstance(c.get("arguments"), dict) and c["arguments"].get("code") == "")
            or c.get("code") == ""
        )
    ]
    assert len(empty_calls) <= 2
    assert result.status in {
        GovernedCapabilityStatus.SUCCESS,
        GovernedCapabilityStatus.NOT_APPLICABLE,
    }


# ---------------- F2: progress from evidence, not op class ------------


def test_f2_analysis_adequate_when_obligation_met():
    _, plan = _read_plan("90260921", evidence=("90260921",))
    hit = _success_attempt(content="structure tree", root="90260921")
    assert (
        classify_investigation_progress(
            hit, plan=plan, operation_class="ANALYSIS"
        )
        == INVESTIGATION_PROGRESS_NEW
    )


def test_f2_read_inadequate_when_obligation_missed():
    _, plan = _read_plan("90260921", evidence=("90260921",))
    miss = _success_attempt(content="other product", root="OTHER")
    assert (
        classify_investigation_progress(
            miss, plan=plan, operation_class="READ"
        )
        == INVESTIGATION_PROGRESS_RELATED
    )


# ---------------- F4: finalize boundary without compulsory plan -------


def test_f4_simple_read_stays_success_with_coverage_unknown():
    only = _success_attempt(content="estrutura MAT-1", root="MAT-1")
    result = _finalize_agent_collected_attempts(
        _gates(),
        input_text="estrutura MAT-1",
        collected=(only,),
        correlation="f4a",
        workspace_context=None,
        deadline=TurnDeadline.start(30.0),
        unbound_outcome=None,
        plan=None,
    )
    assert result.status is GovernedCapabilityStatus.SUCCESS
    assert "coverage_unknown" in result.limitations


def test_f4_related_aggregate_with_plan_does_not_satisfy_list_obligation():
    gates, plan = _read_plan("PROC-REGISTRY", evidence=("PROC-REGISTRY",))
    aggregate = _success_attempt(
        content="KPI totals only",
        root="KPI-SUM",
        structured={"data": {"root": {"code": "KPI-SUM"}, "kpis": [1]}},
    )
    result = _finalize_agent_collected_attempts(
        gates,
        input_text="liste o cadastro de processos",
        collected=(aggregate,),
        correlation="f4b",
        workspace_context=None,
        deadline=TurnDeadline.start(30.0),
        unbound_outcome=OWNER_PATH_UNBOUND,
        plan=plan,
    )
    assert result.status is GovernedCapabilityStatus.NOT_APPLICABLE
    assert "related_observations_insufficient" in result.limitations


def test_f4_plan_satisfied_has_no_coverage_unknown():
    gates, plan = _read_plan("MAT-1", evidence=("MAT-1",))
    only = _success_attempt(content="estrutura MAT-1", root="MAT-1")
    result = _finalize_agent_collected_attempts(
        gates,
        input_text="estrutura MAT-1",
        collected=(only,),
        correlation="f4c",
        workspace_context=None,
        deadline=TurnDeadline.start(30.0),
        unbound_outcome=None,
        plan=plan,
    )
    assert result.status is GovernedCapabilityStatus.SUCCESS
    assert "coverage_unknown" not in result.limitations


# ---------------- F3: real Agent path + metamorphic rename ------------


def _registry_surface(remote_registry: str, remote_aggregate: str):
    """Two capabilities with distinct semantic descriptions, renamed remotes."""
    registry = ProviderCapability(
        capability_id=f"alpha:{remote_registry}",
        group_id="alpha",
        provider_id="pa",
        remote_name=remote_registry,
        owner="alpha",
        operation_class=SpecialistOperationClass.READ,
        description=(
            "List registered process records from the owner registry. "
            "Returns enumerated business rows with registry codes."
        ),
        input_schema={
            "type": "object",
            "properties": {"query": {"type": "string"}},
        },
    )
    aggregate = ProviderCapability(
        capability_id=f"alpha:{remote_aggregate}",
        group_id="alpha",
        provider_id="pa",
        remote_name=remote_aggregate,
        owner="alpha",
        operation_class=SpecialistOperationClass.ANALYSIS,
        description=(
            "Return aggregate KPI summaries for processes. "
            "Does not enumerate registry rows."
        ),
        input_schema={
            "type": "object",
            "properties": {"query": {"type": "string"}},
        },
    )
    provider = FakeProvider(
        "pa",
        [_group("pa", "alpha", [registry, aggregate])],
        outcomes={},
    )
    return provider, registry, aggregate


def _select_by_description(catalog, needle: str) -> str:
    needle_cf = needle.casefold()
    for entry in catalog:
        desc = str(entry.get("description") or "").casefold()
        if needle_cf in desc:
            return str(entry["capability_id"])
    raise AssertionError(f"no capability matching {needle!r} in {catalog}")


def _run_agent_selection_scenario(remote_registry: str, remote_aggregate: str):
    provider, registry, aggregate = _registry_surface(
        remote_registry, remote_aggregate
    )
    gates = _gates(providers=[provider])
    servers = {
        "alpha": owner_tool_server(
            "alpha",
            {
                remote_registry: registry.description or "",
                remote_aggregate: aggregate.description or "",
            },
        )
    }
    invoked: list[str] = []

    def _invoke(**kwargs):
        cap = str(kwargs.get("capability_id") or "")
        invoked.append(cap)
        if cap.endswith(remote_aggregate) or remote_aggregate in cap:
            return _success_attempt(
                content="KPI totals",
                root="KPI-SUM",
                structured={"data": {"root": {"code": "KPI-SUM"}}},
            )
        return _success_attempt(
            content="process A; process B",
            root="PROC-REGISTRY",
        )

    gates._governed_semantic_tool_invoke = _invoke  # type: ignore[method-assign]
    catalog = gates._project_semantic_tool_catalog(
        correlation="f3",
        deadline=TurnDeadline.start(30.0),
        actor_user_id="u1",
    )
    registry_id = _select_by_description(catalog, "enumerated business rows")
    aggregate_id = _select_by_description(catalog, "aggregate kpi")

    def _fn(messages, _info):
        prior = sum(1 for m in messages if isinstance(m, ModelResponse))
        if prior == 0:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        "declare_investigation_goal",
                        {
                            "goal_class": "read",
                            "comparison_requested": False,
                            "target_identities": ["PROC-REGISTRY"],
                            "evidence_needed": ["PROC-REGISTRY"],
                        },
                    )
                ]
            )
        if prior == 1:
            # First choose related-but-inadequate aggregate by contract.
            return ModelResponse(
                parts=[ToolCallPart(aggregate_id, {"query": "processos"})]
            )
        if prior == 2:
            # Then the semantically adequate registry capability.
            return ModelResponse(
                parts=[ToolCallPart(registry_id, {"query": "processos"})]
            )
        return ModelResponse(
            parts=[
                ToolCallPart(
                    "final_result",
                    {
                        "schema_version": "1",
                        "status": "complete",
                        "answer": "process A; process B",
                        "evidence_refs": [1],
                        "unmet_obligations": [],
                        "limitations": [],
                    },
                )
            ]
        )

    with native_toolset_stub(servers):
        engine = PydanticAiInvestigationOrchestrator(
            gates, model=FunctionModel(_fn), tool_calls_limit=6
        )
        result = engine.attempt(
            "Quais processos estão cadastrados no registro?"
        )
    return result, invoked, registry_id, aggregate_id


def _cap_matches(invoked_id: str, catalog_id: str) -> bool:
    """Catalog ids may use ':' while invoke projections use '.'."""
    a = invoked_id.replace(":", ".")
    b = catalog_id.replace(":", ".")
    return a == b or invoked_id.endswith(catalog_id.split(":")[-1]) or (
        catalog_id.split(":")[-1] in invoked_id
    )


def test_f3_agent_path_selects_related_then_adequate_capability():
    result, invoked, registry_id, aggregate_id = _run_agent_selection_scenario(
        "enumerate_registry_records", "summarize_process_aggregates"
    )
    agg_hits = [c for c in invoked if _cap_matches(c, aggregate_id)]
    reg_hits = [c for c in invoked if _cap_matches(c, registry_id)]
    assert agg_hits and reg_hits
    assert invoked.index(agg_hits[0]) < invoked.index(reg_hits[0])
    assert result.status is GovernedCapabilityStatus.SUCCESS
    assert "process A" in (result.content or "")


def test_f3_metamorphic_rename_preserves_agent_selection_path():
    """Same semantic contracts under renamed remotes — Agent path still works."""
    result, invoked, registry_id, aggregate_id = _run_agent_selection_scenario(
        "list_cadastro_processos_v2", "kpi_rollup_view_x"
    )
    assert "list_cadastro_processos_v2" in registry_id
    assert "kpi_rollup_view_x" in aggregate_id
    assert any(_cap_matches(c, aggregate_id) for c in invoked)
    assert any(_cap_matches(c, registry_id) for c in invoked)
    assert result.status is GovernedCapabilityStatus.SUCCESS
    # Negative: selecting only aggregate must not satisfy registry obligation.
    provider, registry, aggregate = _registry_surface(
        "list_cadastro_processos_v2", "kpi_rollup_view_x"
    )
    gates = _gates(providers=[provider])
    plan = gates._accept_semantic_investigation_plan(
        goal_class="read",
        comparison_requested=False,
        target_identities=["PROC-REGISTRY"],
        evidence_needed=["PROC-REGISTRY"],
        correlation="f3neg",
    )
    only_agg = _success_attempt(
        content="KPI totals",
        root="KPI-SUM",
        structured={"data": {"root": {"code": "KPI-SUM"}}},
    )
    neg = _finalize_agent_collected_attempts(
        gates,
        input_text="cadastro",
        collected=(only_agg,),
        correlation="f3neg",
        workspace_context=None,
        deadline=TurnDeadline.start(30.0),
        unbound_outcome=OWNER_PATH_UNBOUND,
        plan=plan,
    )
    assert neg.status is GovernedCapabilityStatus.NOT_APPLICABLE
    assert "related_observations_insufficient" in neg.limitations


# ---------------- Security negative (directly impacted) ---------------


def test_security_discovery_still_not_citable_business_evidence():
    from app.application.capability_provision.semantic_capability_support import (
        INVESTIGATION_PROGRESS_DISCOVERY,
        _is_business_evidence_attempt,
    )

    discovery = _success_attempt(
        content="operationId=list path=/x",
        root="CAT",
        limitations=("discovery_metadata_observation",),
    )
    assert not _is_business_evidence_attempt(discovery)
    assert (
        classify_investigation_progress(discovery)
        == INVESTIGATION_PROGRESS_DISCOVERY
    )
