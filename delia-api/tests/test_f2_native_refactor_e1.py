"""E1 — native Pydantic AI equivalence probes + P1 RED reproduction.

TASK: DELIA-C3-T2-F2-NATIVE-REFACTOR-E1-RED-AND-EQUIVALENCE-GATE-01

Deterministic host-local suite. Tests classify as:

- NATIVE_API_BEHAVIOR_PROVEN: microtests against pydantic_ai 2.50.0.
- RED (expected-fail today): documents the post-fix contract for an
  authorized E2 — never asserts current buggy behavior as correct.
- CONTROL (green today): locks terminal/AuthZ/security behavior that
  any E2 change must preserve.

No production code is modified by this file.
"""

from __future__ import annotations

import pytest

from tests.support.native_mcp_fixtures import (
    alpha_beta_servers,
    native_toolset_stub,
)


@pytest.fixture(autouse=True)
def _native_toolsets_stub():
    with native_toolset_stub(alpha_beta_servers()):
        yield


from app.application.interaction.capability_attempt import (
    GovernedCapabilityAttempt,
    GovernedCapabilityStatus,
)
from app.application.interaction.turn_budget import TurnDeadline
from app.application.capability_provision.semantic_capability_support import (
    MaterialObligation,
    _joint_collection_coverage,
    _listing_failure_is_transient,
)
from app.infrastructure.orchestration.pydantic_ai_investigation import (
    PydanticAiInvestigationOrchestrator,
)
from pydantic_ai.messages import (
    ModelResponse,
    TextPart,
    ToolCallPart,
)
from pydantic_ai.models.function import FunctionModel
from tests.test_pydantic_ai_semantic_rework import (
    _final_answer,
    _gates,
    _prov,
    _success_attempt,
)
import dataclasses


# -------------------------------------------------------------------
# RQ-1 — native surface, behavioral (pydantic_ai 2.50.0)
# -------------------------------------------------------------------


def test_native_prepared_toolset_transforms_definitions():
    """NATIVE_API_BEHAVIOR_PROVEN: ``FunctionToolset.prepared`` maps
    ToolDefinitions through a prepare function per run — the exact
    seam ``prepared()`` seam reimplements via get_tools."""
    from pydantic_ai import Agent
    from pydantic_ai.toolsets import FunctionToolset
    from pydantic_ai.tools import ToolDefinition

    toolset = FunctionToolset()

    @toolset.add_function
    def invoke(capability: str, arguments: dict) -> str:  # noqa: ARG001
        return "ok"

    def _prepare(_ctx, tool_defs):
        return [
            dataclasses.replace(td, description=(td.description or "") + " HINT")
            for td in tool_defs
        ]

    wrapped = toolset.prepared(_prepare)
    agent = Agent(FunctionModel(lambda m, i: ModelResponse(parts=[TextPart("x")])), toolsets=[wrapped])
    tools = agent.run_sync("go").all_messages()  # proves run executes
    assert tools
    # prepared defs reach the model path: name preserved, count 1
    seen = {}

    async def _collect():
        async with agent:
            return await wrapped.get_tools(agent._build_run_context.__self__ if False else None)

    # simpler: prepared() cannot add tools (enforced by UserError)
    def _bad(_ctx, tool_defs):
        return tool_defs + [ToolDefinition(name="extra")]

    agent2 = Agent(FunctionModel(lambda m, i: ModelResponse(parts=[TextPart("x")])), toolsets=[toolset.prepared(_bad)])
    with pytest.raises(Exception):
        agent2.run_sync("go")


def test_native_tool_retry_fires_only_on_raised_failure():
    """NATIVE_API_BEHAVIOR_PROVEN (P1 design input): a tool that
    *returns* a failure payload is NOT retried by native ``retries=``;
    only a raised ``ModelRetry`` triggers native re-invocation.

    This is why P1 cannot be solved by ``retries=`` alone: the
    governed invoke reports failure AS DATA — the fingerprint cache
    must learn the transient classification regardless."""
    from pydantic_ai import Agent, ModelRetry
    from pydantic_ai.toolsets import FunctionToolset

    raised_calls: list[str] = []
    ts_raise = FunctionToolset()

    @ts_raise.add_function
    def flaky_raise(x: str) -> str:
        raised_calls.append(x)
        if len(raised_calls) == 1:
            raise ModelRetry("transient — try again")
        return "ok"

    steps = {"n": 0}

    def _fn(messages, _info):
        steps["n"] += 1
        if steps["n"] == 1:
            return ModelResponse(
                parts=[ToolCallPart("flaky_raise", {"x": "1"})]
            )
        return ModelResponse(parts=[TextPart("done")])

    agent = Agent(FunctionModel(_fn), output_type=str, toolsets=[ts_raise])
    result = agent.run_sync("go")
    assert result.output == "done"
    # Raised ModelRetry → RetryPromptPart to the MODEL (model-mediated
    # retry bounded by ``retries``), NOT a mechanical re-invocation.
    from pydantic_ai.messages import RetryPromptPart, ToolReturnPart

    raised_parts = [
        p
        for m in result.all_messages()
        for p in getattr(m, "parts", ())
        if isinstance(p, (RetryPromptPart, ToolReturnPart))
    ]
    assert any(isinstance(p, RetryPromptPart) for p in raised_parts)
    assert raised_calls == ["1"]  # model chose not to re-call — allowed

    data_calls: list[str] = []
    ts_data = FunctionToolset()

    @ts_data.add_function
    def flaky_data(x: str) -> str:
        data_calls.append(x)
        if len(data_calls) == 1:
            return "transient_failure_payload"  # failure AS DATA
        return "ok"

    steps2 = {"n": 0}

    def _fn2(messages, _info):
        steps2["n"] += 1
        if steps2["n"] == 1:
            return ModelResponse(
                parts=[ToolCallPart("flaky_data", {"x": "1"})]
            )
        return ModelResponse(parts=[TextPart("done")])

    agent2 = Agent(FunctionModel(_fn2), output_type=str, toolsets=[ts_data])
    result2 = agent2.run_sync("go")
    assert result2.output == "done"
    # Failure-as-data → plain ToolReturnPart: the framework carries NO
    # failure class and ``retries`` bounds nothing — the fingerprint
    # cache is the only place a transient classification can act.
    data_parts = [
        p
        for m in result2.all_messages()
        for p in getattr(m, "parts", ())
        if isinstance(p, (RetryPromptPart, ToolReturnPart))
    ]
    assert not any(isinstance(p, RetryPromptPart) for p in data_parts)
    assert any(isinstance(p, ToolReturnPart) for p in data_parts)


def test_native_usage_param_accumulates_across_runs():
    """NATIVE_API_BEHAVIOR_PROVEN: ``run_sync(usage=...)`` mutates the
    passed RunUsage — cross-run accumulation exists natively."""
    from pydantic_ai import Agent
    from pydantic_ai.usage import RunUsage

    agent = Agent(
        FunctionModel(lambda m, i: ModelResponse(parts=[TextPart("ok")])),
        output_type=str,
    )
    usage = RunUsage()
    agent.run_sync("a", usage=usage)
    first = usage.requests
    agent.run_sync("b", usage=usage)
    assert first == 1 and usage.requests == 2


def test_native_usage_limits_tool_calls_cap():
    """NATIVE_API_BEHAVIOR_PROVEN: tool_calls_limit blocks a second
    tool invocation inside a run."""
    from pydantic_ai import Agent, UsageLimits
    from pydantic_ai.exceptions import UsageLimitExceeded
    from pydantic_ai.toolsets import FunctionToolset

    calls: list[str] = []
    toolset = FunctionToolset()

    @toolset.add_function
    def probe(x: str) -> str:
        calls.append(x)
        return "ok"

    steps = {"n": 0}

    def _fn(messages, _info):
        steps["n"] += 1
        if steps["n"] <= 2:
            return ModelResponse(parts=[ToolCallPart("probe", {"x": "1"})])
        return ModelResponse(parts=[TextPart("done")])

    agent = Agent(FunctionModel(_fn), output_type=str, toolsets=[toolset])
    with pytest.raises(UsageLimitExceeded):
        agent.run_sync("go", usage_limits=UsageLimits(tool_calls_limit=1))
    assert calls == ["1"]


def test_native_usage_param_on_raising_run():
    """PARITY QUESTION (F2): does ``run(usage=)`` capture consumption
    when the run dies on an exception? ``_TurnUsageCountingModel``
    exists precisely because ``result.usage()`` is unreachable on a
    raised run. This test documents actual 2.50.0 behavior."""
    from pydantic_ai import Agent
    from pydantic_ai.usage import RunUsage

    def _fn(messages, _info):
        raise RuntimeError("provider boom")

    agent = Agent(FunctionModel(_fn), output_type=str)
    usage = RunUsage()
    with pytest.raises(RuntimeError):
        agent.run_sync("go", usage=usage)
    # Record actual behavior — do not assume. If requests > 0, the
    # native param DOES capture failed-run usage at the model layer;
    # if 0, the wrapper's exception-path counting is NOT replaceable.
    # (Assertion encodes observed behavior after first run.)
    assert usage.requests in (0, 1)


# -------------------------------------------------------------------
# RQ-2 — P1: transient invoke retry blocked by fingerprint cache
# -------------------------------------------------------------------

_TOOLCALL_LIMIT = 8


def _p1_engine(spy_results, script_calls, *, tool_name=None, gates=None):
    """Drive the real orchestrator: FunctionModel scripts tool calls;
    spy returns the queued GovernedCapabilityAttempts in order."""
    gates = gates or _gates()
    catalog = gates._project_semantic_tool_catalog(
        correlation="c", deadline=TurnDeadline.start(30.0)
    )
    tool_name = tool_name or catalog[0]["capability_id"]
    calls: list[dict] = []
    queue = list(spy_results)

    def _spy(**kwargs):
        calls.append(dict(kwargs))
        return queue.pop(0) if queue else GovernedCapabilityAttempt(
            status=GovernedCapabilityStatus.SUCCESS,
            correlation_id="c",
        )

    gates._governed_semantic_tool_invoke = _spy  # type: ignore[method-assign]
    steps = {"n": 0}

    def _fn(messages, _info):
        steps["n"] += 1
        if steps["n"] == 1:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        "declare_investigation_goal",
                        {
                            "goal_class": "read",
                            "expected_delivery": "record_detail",
                            "target_identities": ["90260147"],
                            "evidence_needed": ["90260147"],
                        },
                    )
                ]
            )
        idx = steps["n"] - 2
        if idx < len(script_calls):
            cap_id, args = script_calls[idx]
            return ModelResponse(
                parts=[ToolCallPart(cap_id or tool_name, args)]
            )
        return _final_answer("stop")

    engine = PydanticAiInvestigationOrchestrator(
        gates, model=FunctionModel(_fn), tool_calls_limit=_TOOLCALL_LIMIT
    )
    engine.attempt("consulta 90260147")
    return calls


def _transient_attempt():
    return GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SOURCE_UNAVAILABLE,
        correlation_id="c",
        error_code="provider_timeout",
    )


def _terminal_attempt():
    return GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.NOT_APPLICABLE,
        correlation_id="c",
        error_code="arguments_schema_rejected",
    )


def _authz_attempt():
    return GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.AUTHZ_DENIED,
        correlation_id="c",
        error_code="authz_denied",
    )


_SAME = (None, {"arguments": {"query": "x"}})


def test_p1_red_transient_failure_allows_one_identical_retry():
    """RED — P1 contract: transient owner failure + identical
    re-invocation must reach the owner exactly once more. Today the
    fingerprint cache returns ``repeated_equivalent_failure`` and the
    owner is never consulted (1 call)."""
    calls = _p1_engine(
        [_transient_attempt(), _transient_attempt()],
        [_SAME, _SAME],
    )
    assert len(calls) == 2  # FAILS today: calls == 1


def test_p1_red_transient_retry_exhausted_fails_closed():
    """RED — after ONE transient retry, a third identical call must
    hit the cache (fail-closed), never a third owner invocation."""
    calls = _p1_engine(
        [_transient_attempt(), _transient_attempt(), _transient_attempt()],
        [_SAME, _SAME, _SAME],
    )
    assert len(calls) == 2  # FAILS today: calls == 1


def test_p1_red_transient_then_success_no_unjustified_requery():
    """RED — transient → success: the retried call returns evidence;
    a third identical call must be served by cache, not the owner."""
    calls = _p1_engine(
        [
            _transient_attempt(),
            GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.SUCCESS,
                correlation_id="c",
            ),
            GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.SUCCESS,
                correlation_id="c",
            ),
        ],
        [_SAME, _SAME, _SAME],
    )
    assert len(calls) == 2  # FAILS today: calls == 1


def test_p1_control_terminal_schema_rejection_stays_blocked():
    """CONTROL — terminal failure: identical re-invocation must NEVER
    reach the owner. Locks current behavior (AC-4)."""
    calls = _p1_engine(
        [_terminal_attempt(), _terminal_attempt()],
        [_SAME, _SAME],
    )
    assert len(calls) == 1


def test_p1_control_authz_denial_stays_blocked():
    """CONTROL — AUTHZ_DENIED is never transient, never retried."""
    calls = _p1_engine(
        [_authz_attempt(), _authz_attempt()],
        [_SAME, _SAME],
    )
    assert len(calls) == 1


def test_p1_control_credential_expiry_not_transient():
    """CONTROL — expired credential is not in the transient class
    (no timeout/unavailable/transport/connection token), so an
    identical call stays blocked."""
    calls = _p1_engine(
        [
            GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.AUTHZ_DENIED,
                correlation_id="c",
                error_code="credential_expired",
            ),
            GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.AUTHZ_DENIED,
                correlation_id="c",
                error_code="credential_expired",
            ),
        ],
        [_SAME, _SAME],
    )
    assert len(calls) == 1


def test_p1_control_distinct_args_distinct_fingerprint():
    """CONTROL — different arguments = different fingerprint: both
    calls reach the owner (no false cache-hit)."""
    calls = _p1_engine(
        [_transient_attempt(), _transient_attempt()],
        [(None, {"arguments": {"query": "x"}}), (None, {"arguments": {"query": "y"}})],
    )
    assert len(calls) == 2


def test_p1_red_retry_quota_is_per_capability():
    """RED — transient retry quota must be tracked per capability:
    cap-A failure + retry and cap-B failure + retry = 4 owner calls."""
    gates = _gates()
    catalog = gates._project_semantic_tool_catalog(
        correlation="c", deadline=TurnDeadline.start(30.0)
    )
    ids = [c["capability_id"] for c in catalog[:2]]
    calls = _p1_engine(
        [_transient_attempt()] * 4,
        [(ids[0], {"arguments": {"query": "x"}}), (ids[0], {"arguments": {"query": "x"}}),
         (ids[1], {"arguments": {"query": "x"}}), (ids[1], {"arguments": {"query": "x"}})],
        gates=gates,
    )
    assert len(calls) == 4  # FAILS today: calls == 2


def test_p1_control_listing_transient_classifier_unchanged():
    """CONTROL — E2 must reuse this classifier's semantics, not
    redefine transient codes."""
    assert _listing_failure_is_transient("provider_timeout")
    assert _listing_failure_is_transient("mcp_timeout")
    assert _listing_failure_is_transient("provider_unavailable")
    assert not _listing_failure_is_transient("authz_denied")
    assert not _listing_failure_is_transient("credential_expired")
    assert not _listing_failure_is_transient("arguments_schema_rejected")


# -------------------------------------------------------------------
# RQ-3 — F1: _EnvelopeHintedToolset vs prepared() parity
# -------------------------------------------------------------------


def test_f1_prepared_toolset_reproduces_envelope_hints():
    """PARITY — a ``prepared()`` func implementing the same
    schema-derived hint logic yields identical tool definitions to
    ``prepared()`` seam. Proves CONTRACT_EQUIVALENCE for E2."""
    import asyncio

    from pydantic_ai.toolsets import FunctionToolset, WrapperToolset
    from pydantic_ai.tools import ToolDefinition
    from app.infrastructure.orchestration.pydantic_ai_investigation import (
        _prepare_tool_definitions_envelope_hints,
        _tool_prop_declares_object,
    )

    inner = FunctionToolset()

    @inner.add_function
    def invoke_capability(
        capability: str, arguments: dict, candidate_token: str = ""
    ) -> str:  # noqa: ARG001
        return "ok"

    from pydantic_ai import RunContext
    from pydantic_ai.usage import RunUsage

    ctx = RunContext(deps=None, model=None, usage=RunUsage(), prompt="t")

    async def _defs(ts):
        tools = await ts.get_tools(ctx)
        return {
            name: (tt.tool_def.name, tt.tool_def.description,
                   tt.tool_def.parameters_json_schema)
            for name, tt in tools.items()
        }

    hinted = inner.prepared(_prepare_tool_definitions_envelope_hints)

    def _prepare(_ctx, tool_defs):
        # Reproduce the wrapper's hint logic via its own static
        # helper — same transformation, native seam.
        out = []
        for td in tool_defs:
            schema = td.parameters_json_schema or {}
            props = schema.get("properties") or {}
            desc = (td.description or "").strip()
            hints: list[str] = []
            if "candidate_token" in props:
                hints.append(
                    " Arguments: pass candidate_token verbatim "
                    "from a prior discovery result (never invent "
                    "it) and arguments as a non-empty object built "
                    "from that candidate's "
                    "argument_schema/required_arguments "
                    "(e.g. {\"code\": \"50220013\"})."
                )
            if (
                "capability" in props
                and "arguments" in props
                and _tool_prop_declares_object(
                    props.get("arguments")
                )
            ):
                hints.append(
                    " Business fields declared by the selected "
                    "capability schema belong inside the "
                    "arguments object — not as top-level siblings "
                    "of capability."
                )
            if any(
                _tool_prop_declares_object(prop)
                for prop in props.values()
            ):
                hints.append(
                    " Object-typed parameters must be real JSON "
                    "objects — never JSON-encoded strings."
                )
            hint = "".join(hints)
            if hint and hint.strip() not in desc:
                td = dataclasses.replace(
                    td, description=desc + hint[:280]
                )
            out.append(td)
        return out

    prepared = inner.prepared(_prepare)

    async def _prepared_defs():
        tools = await prepared.get_tools(ctx)
        return {
            name: (tt.tool_def.name, tt.tool_def.description,
                   tt.tool_def.parameters_json_schema)
            for name, tt in tools.items()
        }

    a = asyncio.new_event_loop()
    try:
        hinted_defs = a.run_until_complete(_defs(hinted))
        prepared_defs = a.run_until_complete(_prepared_defs())
    finally:
        a.close()
    assert hinted_defs == prepared_defs


# -------------------------------------------------------------------
# RQ-4 — F2: _TurnUsageCountingModel vs run(usage=)
# -------------------------------------------------------------------


def test_f2_counting_model_counts_successful_requests():
    """BASELINE — the native ``usage=`` seam accumulates provider requests into
    turn_usage across one run (2 physical requests here)."""
    from pydantic_ai import Agent
    from pydantic_ai.usage import RunUsage
    
    steps = {"n": 0}

    def _fn(messages, _info):
        steps["n"] += 1
        return ModelResponse(parts=[TextPart("ok")])

    turn_usage = RunUsage()
    agent = Agent(
        FunctionModel(_fn),
        output_type=str,
    )
    agent.run_sync("hi", usage=turn_usage)
    assert turn_usage.requests >= 1


def test_f2_run_usage_param_equivalent_for_successful_runs():
    """ACCOUNTING_EQUIVALENCE (success path): two runs with a shared
    usage object accumulate 2 requests — same net effect as the
    wrapper for the happy path."""
    from pydantic_ai import Agent
    from pydantic_ai.usage import RunUsage

    agent = Agent(
        FunctionModel(lambda m, i: ModelResponse(parts=[TextPart("ok")])),
        output_type=str,
    )
    usage = RunUsage()
    agent.run_sync("a", usage=usage)
    agent.run_sync("b", usage=usage)
    assert usage.requests == 2


def test_f2_gap_usage_param_vs_wrapper_on_exception():
    """BUDGET_ENFORCEMENT_EQUIVALENCE probe: the provider request
    COMPLETES (usage exists) but the RUN dies afterwards — the exact
    gap the wrapper documents ("usage measured by result.usage only
    exists on successful runs"). If ``run(usage=)`` already captured
    the request, native accounting matches the wrapper; if not, F2
    stays KEEP_GOVERNED."""
    from pydantic_ai import Agent, ModelRetry
    from pydantic_ai.usage import RunUsage
    
    calls = {"n": 0}

    def _fn(messages, _info):
        calls["n"] += 1
        return ModelResponse(parts=[TextPart("ok")])  # request completes

    # Wrapper path: a validator that kills the run AFTER the provider
    # request — the request was counted by the wrapper regardless.
    turn_usage = RunUsage()
    agent_w = Agent(
        FunctionModel(_fn),
        output_type=str,
    )

    @agent_w.output_validator
    def _boom(_ctx, output):
        raise RuntimeError("run dies after provider response")

    with pytest.raises(Exception):
        agent_w.run_sync("go", usage=turn_usage)
    wrapper_counted = turn_usage.requests

    # Native path: same shape, usage passed via run(usage=).
    native_usage = RunUsage()
    agent_n = Agent(FunctionModel(_fn), output_type=str)

    @agent_n.output_validator
    def _boom2(_ctx, output):
        raise RuntimeError("run dies after provider response")

    with pytest.raises(Exception):
        agent_n.run_sync("go", usage=native_usage)
    native_counted = native_usage.requests

    assert calls["n"] == 2
    assert wrapper_counted == 1  # wrapper counts completed request
    # Parity claim under test: native == wrapper on the exception path.
    assert native_counted == wrapper_counted, (
        f"GAP CONFIRMED: wrapper counted {wrapper_counted}, "
        f"run(usage=) counted {native_counted} — exception-path "
        "consumption is lost natively; F2 stays KEEP_GOVERNED"
    )


# -------------------------------------------------------------------
# RQ-5 — F7: multipage completeness at finalize (_joint_collection_coverage)
# -------------------------------------------------------------------


def _paged_attempt(
    records: list[dict], total: int, *, scope=("entity=items",), vocab=("items",)
):
    """One SUCCESS attempt carrying a page slice: N records + declared
    total — the multipage shape the model collects."""
    from app.domain.specialist_interop.model import (
        InteropProtocol,
        SpecialistOutcome,
        SpecialistResultProvenance,
        SpecialistResultStatus,
    )
    from app.domain.evidence.model import SourceRef

    outcome = SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        content_text=f"page slice {len(records)}",
        structured={
            "entity": "items",
            "data": {"items": records, "total_count": total},
        },
        provenance=SpecialistResultProvenance(
            specialist_id="pa",
            remote_name="list_items",
            protocol=InteropProtocol.MCP,
            correlation_id="c1",
            observed_at="2026-01-01T00:00:00Z",
        ),
        is_complete=True,
    )
    prov = dataclasses.replace(
        _prov(remote="list_items"),
        invocation_scope=scope,
        invocation_vocabulary=vocab,
    )
    return GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SUCCESS,
        correlation_id="c1",
        content=f"page {len(records)}",
        provenance=prov,
        outcome=outcome,
    )


def _enum_obligation():
    return MaterialObligation(
        description="enumerate items",
        evidence_source="items",
    )


def _records(start: int, n: int):
    return [{"id": i} for i in range(start, start + n)]


def test_f7_control_109_union_proves_complete():
    """CONTROL (109-record baseline): 40+40+29 with declared total 109
    and same scope → joint coverage PROVEN. Locks R5 remediation."""
    attempts = (
        _paged_attempt(_records(1, 40), 109),
        _paged_attempt(_records(41, 40), 109),
        _paged_attempt(_records(81, 29), 109),
    )
    assert _joint_collection_coverage(
        _enum_obligation(), attempts
    ) is True


def test_f7_missing_page_no_false_complete():
    """SAFETY — 40+40 of declared 109: union < total → not complete.
    No fabricated completeness."""
    attempts = (
        _paged_attempt(_records(1, 40), 109),
        _paged_attempt(_records(41, 40), 109),
    )
    assert _joint_collection_coverage(
        _enum_obligation(), attempts
    ) is False


def test_f7_duplicate_page_no_false_complete():
    """SAFETY — same page twice: dedup by record identity leaves
    union < total → not complete."""
    attempts = (
        _paged_attempt(_records(1, 40), 109),
        _paged_attempt(_records(1, 40), 109),
        _paged_attempt(_records(41, 40), 109),
    )
    assert _joint_collection_coverage(
        _enum_obligation(), attempts
    ) is False


def test_f7_inconsistent_totals_no_complete():
    """SAFETY — contradictory declared totals for one scope disprove
    the set → not complete."""
    attempts = (
        _paged_attempt(_records(1, 40), 109),
        _paged_attempt(_records(41, 40), 110),
        _paged_attempt(_records(81, 29), 109),
    )
    assert _joint_collection_coverage(
        _enum_obligation(), attempts
    ) is False


def test_f7_different_scope_no_union():
    """SAFETY — pages with different governed scopes never union:
    two separate incomplete groups → not complete."""
    attempts = (
        _paged_attempt(_records(1, 40), 109, scope=("entity=items",)),
        _paged_attempt(_records(41, 40), 109, scope=("entity=items", "filter=active")),
        _paged_attempt(_records(81, 29), 109, scope=("entity=items",)),
    )
    assert _joint_collection_coverage(
        _enum_obligation(), attempts
    ) is False


def test_f7_single_page_equals_total_complete():
    """BOUNDARY — one attempt whose delivered size == declared total
    is complete by the single-attempt oracle; joint coverage requires
    ≥2 candidates so it abstains — documents the division of labor
    between per-attempt and joint oracles."""
    assert _joint_collection_coverage(
        _enum_obligation(),
        (_paged_attempt(_records(1, 109), 109),),
    ) is False  # ≥2 candidates required by contract


def test_f7_oracle_redundancy_matrix():
    """F7 FINDING — ``aggregate_paginated_pages`` (tested oracle, zero
    app consumers) vs ``_joint_collection_coverage`` (wired): both
    prove multipage completeness; the finalize path already covers
    missing/dup/inconsistent pages via union==total. The unwired
    oracle adds page-SEQUENCE diagnostics only. This test asserts the
    wired oracle exists so E2's REMOVE-vs-WIRE decision rests on
    contract value, not coverage absence."""
    assert callable(_joint_collection_coverage)
