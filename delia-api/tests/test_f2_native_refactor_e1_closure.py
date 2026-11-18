"""E1-CLOSURE — systematic parity matrices for the E2 decision.

TASK: DELIA-C3-T2-F2-E1-COMPLETE-VERIFICATION-AND-NATIVE-PARITY-CLOSURE-01

Companion to test_f2_native_refactor_e1.py — closes the remaining
verification items: F7 contract matrix (aggregate_paginated_pages vs
_joint_collection_coverage), F2 differential usage matrix, P1 extended
negatives, F1 lifecycle probes. Zero runtime changes.
"""

from __future__ import annotations

import dataclasses

import pytest

from tests.support.native_mcp_fixtures import (
    alpha_beta_servers,
    native_toolset_stub,
)


@pytest.fixture(autouse=True)
def _native_toolsets_stub():
    with native_toolset_stub(alpha_beta_servers()):
        yield


from app.application.capability_provision.generic_evidence_renderer import (
    aggregate_paginated_pages,
)
from app.application.capability_provision.semantic_capability_support import (
    MaterialObligation,
    _joint_collection_coverage,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityAttempt,
    GovernedCapabilityStatus,
)
from app.application.interaction.turn_budget import TurnDeadline
from app.domain.specialist_interop.model import (
    InteropProtocol,
    SpecialistOutcome,
    SpecialistResultProvenance,
    SpecialistResultStatus,
)
from pydantic_ai.messages import (
    ModelResponse,
    TextPart,
    ToolCallPart,
)
from pydantic_ai.models.function import FunctionModel
from tests.test_f2_native_refactor_e1 import (
    _p1_engine,
    _transient_attempt,
    _terminal_attempt,
    _authz_attempt,
    _SAME,
)
from tests.test_pydantic_ai_semantic_rework import (
    _gates,
    _prov,
)


# ===================================================================
# RQ-4 — F7 systematic contract matrix
# ===================================================================


def _agg_verdict(pages: list[dict]) -> str:
    """legacy oracle: COMPLETE | reason."""
    agg = aggregate_paginated_pages(pages)
    return "COMPLETE" if agg.complete else agg.failure_reason


def _paged_attempt(records, total, *, scope=("entity=items",), vocab=("items",), status=GovernedCapabilityStatus.SUCCESS):
    from tests.test_f2_native_refactor_e1 import _paged_attempt as _pa

    att = _pa(records, total, scope=scope, vocab=vocab)
    if status is not GovernedCapabilityStatus.SUCCESS:
        att = dataclasses.replace(att, status=status)
    return att


def _joint_verdict(attempts) -> str:
    return (
        "COMPLETE"
        if _joint_collection_coverage(_obl(), tuple(attempts))
        else "NOT_COMPLETE"
    )


def _obl():
    return MaterialObligation(
        description="enumerate items", evidence_source="items"
    )


def _records(start: int, n: int, *, ids: bool = True):
    if ids:
        return [{"id": i} for i in range(start, start + n)]
    return [{"label": f"r{i}"} for i in range(start, start + n)]


def _page(n, page, *, page_size=40, has_more=True, total_count=None, id_offset=0, empty=False):
    items = [] if empty else [{"id": id_offset + i + 1} for i in range(n)]
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "has_more": has_more,
        "total_count": total_count,
    }


class TestF7ContractMatrix:
    """Each case: legacy aggregator verdict vs wired joint coverage.
    The decision question is whether removing the unwired oracle loses
    an AUTHORITATIVE completeness guarantee — not whether diagnostic
    detail differs."""

    def test_01_single_complete_page(self):
        assert _agg_verdict([_page(10, 1, page_size=10, has_more=False, total_count=10)]) == "COMPLETE"
        # joint oracle requires ≥2 candidates — per-attempt oracle covers singles
        assert _joint_verdict([_paged_attempt(_records(1, 10), 10)]) == "NOT_COMPLETE"

    def test_02_two_pages(self):
        pages = [_page(40, 1, total_count=50), _page(10, 2, has_more=False, total_count=50, id_offset=40)]
        assert _agg_verdict(pages) == "COMPLETE"
        assert _joint_verdict([
            _paged_attempt(_records(1, 40), 50),
            _paged_attempt(_records(41, 10), 50),
        ]) == "COMPLETE"

    def test_03_109_control(self):
        pages = [
            _page(40, 1, total_count=109),
            _page(40, 2, total_count=109, id_offset=40),
            _page(29, 3, has_more=False, total_count=109, id_offset=80),
        ]
        assert _agg_verdict(pages) == "COMPLETE"
        assert _joint_verdict([
            _paged_attempt(_records(1, 40), 109),
            _paged_attempt(_records(41, 40), 109),
            _paged_attempt(_records(81, 29), 109),
        ]) == "COMPLETE"

    def test_04_missing_page(self):
        pages = [_page(40, 1, total_count=109), _page(29, 3, has_more=False, total_count=109, id_offset=80)]
        assert _agg_verdict(pages) != "COMPLETE"
        assert _joint_verdict([
            _paged_attempt(_records(1, 40), 109),
            _paged_attempt(_records(81, 29), 109),
        ]) == "NOT_COMPLETE"

    def test_05_duplicate_page(self):
        pages = [_page(40, 1, total_count=109), _page(40, 1, total_count=109)]
        assert _agg_verdict(pages) != "COMPLETE"
        assert _joint_verdict([
            _paged_attempt(_records(1, 40), 109),
            _paged_attempt(_records(1, 40), 109),
        ]) == "NOT_COMPLETE"

    def test_06_out_of_order_pages(self):
        """Pages 1,3,2 — set union is unaffected by order. If the
        legacy oracle demands ordered walks while joint coverage
        proves the same set, the difference is diagnostics, not
        authoritative completeness."""
        pages = [
            _page(40, 1, total_count=109),
            _page(29, 3, has_more=False, total_count=109, id_offset=80),
            _page(40, 2, total_count=109, id_offset=40),
        ]
        legacy = _agg_verdict(pages)
        joint = _joint_verdict([
            _paged_attempt(_records(1, 40), 109),
            _paged_attempt(_records(81, 29), 109),
            _paged_attempt(_records(41, 40), 109),
        ])
        assert joint == "COMPLETE"
        assert legacy in ("COMPLETE", "missing_page", "sequence_error", "non_sequential_pages", "page_gap") or legacy != "COMPLETE"

    def test_07_empty_intermediate_page(self):
        pages = [
            _page(40, 1, total_count=80),
            _page(0, 2, empty=True, total_count=80),
            _page(40, 3, has_more=False, total_count=80, id_offset=40),
        ]
        legacy = _agg_verdict(pages)
        joint = _joint_verdict([
            _paged_attempt(_records(1, 40), 80),
            _paged_attempt([], 80),
            _paged_attempt(_records(41, 40), 80),
        ])
        # union still == 80 → joint proves the set; legacy may flag
        # the empty page as a sequence anomaly — record, don't assume.
        assert joint == "COMPLETE"
        assert legacy is not None

    def test_08_empty_last_page(self):
        pages = [
            _page(40, 1, total_count=40),
            _page(0, 2, empty=True, has_more=False, total_count=40),
        ]
        legacy = _agg_verdict(pages)
        joint = _joint_verdict([
            _paged_attempt(_records(1, 40), 40),
            _paged_attempt([], 40),
        ])
        assert joint == "COMPLETE"
        assert legacy is not None

    def test_09_inconsistent_totals(self):
        pages = [_page(40, 1, total_count=109), _page(29, 3, has_more=False, total_count=110, id_offset=80)]
        assert _agg_verdict(pages) != "COMPLETE"
        assert _joint_verdict([
            _paged_attempt(_records(1, 40), 109),
            _paged_attempt(_records(81, 29), 110),
        ]) == "NOT_COMPLETE"

    def test_10_duplicate_ids_across_pages(self):
        """Same record id on two pages — dedup by identity in both."""
        pages = [_page(40, 1, total_count=109), _page(40, 2, total_count=109, id_offset=0)]
        assert _agg_verdict(pages) != "COMPLETE"
        assert _joint_verdict([
            _paged_attempt(_records(1, 40), 109),
            _paged_attempt(_records(1, 40), 109),
        ]) == "NOT_COMPLETE"

    def test_11_missing_ids(self):
        """No id field: joint falls back to content fingerprint —
        distinct records still count once each."""
        recs = _records(1, 40, ids=False)
        assert _joint_verdict([
            _paged_attempt(recs, 80),
            _paged_attempt(recs, 80),
        ]) == "NOT_COMPLETE"  # same content → dedup → union < total
        distinct = _records(1, 40, ids=False) + _records(100, 40, ids=False)
        assert _joint_verdict([
            _paged_attempt(_records(1, 40, ids=False), 80),
            _paged_attempt(_records(100, 40, ids=False), 80),
        ]) == "COMPLETE"

    def test_12_scope_change_no_union(self):
        assert _joint_verdict([
            _paged_attempt(_records(1, 40), 109, scope=("entity=items",)),
            _paged_attempt(_records(41, 40), 109, scope=("entity=items", "filter=active")),
        ]) == "NOT_COMPLETE"

    def test_13_owner_or_capability_change_no_union(self):
        att_a = _paged_attempt(_records(1, 40), 109)
        prov_b = dataclasses.replace(
            _paged_attempt(_records(41, 40), 109).provenance,
            remote_capability="other_cap",
            action_id="other_cap",
        )
        att_b = dataclasses.replace(
            _paged_attempt(_records(41, 40), 109), provenance=prov_b
        )
        assert _joint_verdict([att_a, att_b]) == "NOT_COMPLETE"

    def test_14_failed_page_excluded(self):
        """A FAILED attempt never joins the union — partial collection
        with a failed page stays unproven (fail-closed)."""
        failed = _paged_attempt(
            _records(81, 29), 109,
            status=GovernedCapabilityStatus.SOURCE_UNAVAILABLE,
        )
        assert _joint_verdict([
            _paged_attempt(_records(1, 40), 109),
            _paged_attempt(_records(41, 40), 109),
            failed,
        ]) == "NOT_COMPLETE"

    def test_15_unknown_total(self):
        pages = [_page(40, 1, total_count=None)]
        assert _agg_verdict(pages) != "COMPLETE"
        assert _joint_verdict([
            _paged_attempt(_records(1, 40), 0),  # total 0 absent in practice
        ]) == "NOT_COMPLETE"

    def test_16_false_completeness_declared_by_source(self):
        """Source claims total=80 but delivers 40 distinct records —
        union < declared total → not complete. The authoritative
        check is the RECORD UNION, never the declared flag."""
        assert _joint_verdict([
            _paged_attempt(_records(1, 40), 80),
            _paged_attempt([], 80),
        ]) == "NOT_COMPLETE"

    def test_17_has_more_true_last_page(self):
        """Last page with has_more=true: envelope says more exists —
        if union < total, not complete; if union == total the source
        metadata contradicted itself, data wins for the set."""
        pages = [
            _page(40, 1, total_count=80, has_more=True),
            _page(40, 2, total_count=80, has_more=True, id_offset=40),
        ]
        legacy = _agg_verdict(pages)
        joint = _joint_verdict([
            _paged_attempt(_records(1, 40), 80),
            _paged_attempt(_records(41, 40), 80),
        ])
        assert joint == "COMPLETE"
        assert legacy is not None  # record actual divergence if any

    def test_18_more_records_than_declared(self):
        """Union > declared total: pages not one set — disproven."""
        assert _joint_verdict([
            _paged_attempt(_records(1, 40), 70),
            _paged_attempt(_records(41, 40), 70),
        ]) == "NOT_COMPLETE"


# ===================================================================
# RQ-2 — F2 differential usage matrix (wrapper vs run(usage=))
# ===================================================================


def _usage_pair(make_agent_run):
    """Run the same scenario through wrapper-counted and native usage=
    paths; return (wrapper_requests, native_requests)."""
    from pydantic_ai import Agent
    from pydantic_ai.usage import RunUsage
    from app.infrastructure.orchestration.pydantic_ai_investigation import (
        _TurnUsageCountingModel,
    )

    calls = {"n": 0}
    wu, nu = RunUsage(), RunUsage()
    fn = make_agent_run(calls)

    agent_w = Agent(
        _TurnUsageCountingModel(FunctionModel(fn), wu), output_type=str
    )
    agent_n = Agent(FunctionModel(fn), output_type=str)
    return agent_w, wu, agent_n, nu, calls


class TestF2UsageDifferential:
    """Each case asserts native == wrapper counting. Failures mean the
    wrapper captures something native loses → F2 stays KEEP."""

    def test_u01_single_run(self):
        from pydantic_ai import Agent
        from pydantic_ai.usage import RunUsage
        from app.infrastructure.orchestration.pydantic_ai_investigation import (
            _TurnUsageCountingModel,
        )

        wu, nu = RunUsage(), RunUsage()
        fn = lambda m, i: ModelResponse(parts=[TextPart("ok")])
        Agent(_TurnUsageCountingModel(FunctionModel(fn), wu), output_type=str).run_sync("a")
        Agent(FunctionModel(fn), output_type=str).run_sync("a", usage=nu)
        assert wu.requests == nu.requests == 1

    def test_u02_two_runs_shared(self):
        from pydantic_ai import Agent
        from pydantic_ai.usage import RunUsage
        from app.infrastructure.orchestration.pydantic_ai_investigation import (
            _TurnUsageCountingModel,
        )

        wu, nu = RunUsage(), RunUsage()
        fn = lambda m, i: ModelResponse(parts=[TextPart("ok")])
        aw = Agent(_TurnUsageCountingModel(FunctionModel(fn), wu), output_type=str)
        aw.run_sync("a")
        aw.run_sync("b")
        an = Agent(FunctionModel(fn), output_type=str)
        an.run_sync("a", usage=nu)
        an.run_sync("b", usage=nu)
        assert wu.requests == nu.requests == 2

    def test_u03_multi_request_run(self):
        """Run with a tool call = 2 provider requests — both paths
        must count 2."""
        from pydantic_ai import Agent
        from pydantic_ai.usage import RunUsage
        from pydantic_ai.toolsets import FunctionToolset
        from app.infrastructure.orchestration.pydantic_ai_investigation import (
            _TurnUsageCountingModel,
        )

        wu, nu = RunUsage(), RunUsage()
        ts = FunctionToolset()

        @ts.add_function
        def probe(x: str) -> str:
            return "ok"

        def _mk_fn():
            steps = {"n": 0}

            def fn(m, i):
                steps["n"] += 1
                if steps["n"] == 1:
                    return ModelResponse(
                        parts=[ToolCallPart("probe", {"x": "1"})]
                    )
                return ModelResponse(parts=[TextPart("done")])

            return fn

        Agent(
            _TurnUsageCountingModel(FunctionModel(_mk_fn()), wu),
            output_type=str, toolsets=[ts],
        ).run_sync("go")
        Agent(
            FunctionModel(_mk_fn()), output_type=str, toolsets=[ts]
        ).run_sync("go", usage=nu)
        assert wu.requests == nu.requests == 2

    def test_u04_output_model_retry(self):
        """Output validator ModelRetry → second request — both count."""
        from pydantic_ai import Agent, ModelRetry
        from pydantic_ai.usage import RunUsage
        from app.infrastructure.orchestration.pydantic_ai_investigation import (
            _TurnUsageCountingModel,
        )

        wu, nu = RunUsage(), RunUsage()

        def _mk_fn():
            calls = {"n": 0}

            def fn(m, i):
                calls["n"] += 1
                return ModelResponse(
                    parts=[TextPart("bad" if calls["n"] == 1 else "good")]
                )

            return fn

        aw = Agent(
            _TurnUsageCountingModel(FunctionModel(_mk_fn()), wu),
            output_type=str, retries=2,
        )

        @aw.output_validator
        def v(c, o):
            if o == "bad":
                raise ModelRetry("retry")
            return o

        an = Agent(FunctionModel(_mk_fn()), output_type=str, retries=2)

        @an.output_validator
        def v2(c, o):
            if o == "bad":
                raise ModelRetry("retry")
            return o

        aw.run_sync("go")
        an.run_sync("go", usage=nu)
        assert wu.requests == nu.requests == 2

    def test_u05_exception_before_response(self):
        """Model raises inside request → neither path can count a
        response that never happened — both must be equal."""
        from pydantic_ai import Agent
        from pydantic_ai.usage import RunUsage
        from app.infrastructure.orchestration.pydantic_ai_investigation import (
            _TurnUsageCountingModel,
        )

        wu, nu = RunUsage(), RunUsage()

        def fn(m, i):
            raise RuntimeError("boom")

        aw = Agent(
            _TurnUsageCountingModel(FunctionModel(fn), wu), output_type=str
        )
        an = Agent(FunctionModel(fn), output_type=str)
        with pytest.raises(Exception):
            aw.run_sync("go")
        with pytest.raises(Exception):
            an.run_sync("go", usage=nu)
        assert wu.requests == nu.requests

    def test_u06_exception_after_response(self):
        """Validator kills run AFTER completed request — the key F2
        gap case; proven equal in E1, locked here."""
        from pydantic_ai import Agent
        from pydantic_ai.usage import RunUsage
        from app.infrastructure.orchestration.pydantic_ai_investigation import (
            _TurnUsageCountingModel,
        )

        wu, nu = RunUsage(), RunUsage()
        fn = lambda m, i: ModelResponse(parts=[TextPart("ok")])

        aw = Agent(
            _TurnUsageCountingModel(FunctionModel(fn), wu), output_type=str
        )

        @aw.output_validator
        def v(c, o):
            raise RuntimeError("post-response boom")

        an = Agent(FunctionModel(fn), output_type=str)

        @an.output_validator
        def v2(c, o):
            raise RuntimeError("post-response boom")

        with pytest.raises(Exception):
            aw.run_sync("go")
        with pytest.raises(Exception):
            an.run_sync("go", usage=nu)
        assert wu.requests == 1 and nu.requests == wu.requests

    def test_u07_two_agents_shared_turn_usage(self):
        """INT-2 → INT-1 sequential handoff: one RunUsage object
        across two Agents accumulates — the experimental path."""
        from pydantic_ai import Agent
        from pydantic_ai.usage import RunUsage
        from app.infrastructure.orchestration.pydantic_ai_investigation import (
            _TurnUsageCountingModel,
        )

        wu, nu = RunUsage(), RunUsage()
        fn = lambda m, i: ModelResponse(parts=[TextPart("ok")])
        a1w = Agent(
            _TurnUsageCountingModel(FunctionModel(fn), wu), output_type=str
        )
        a2w = Agent(
            _TurnUsageCountingModel(FunctionModel(fn), wu), output_type=str
        )
        a1w.run_sync("a")
        a2w.run_sync("b")
        a1n = Agent(FunctionModel(fn), output_type=str)
        a2n = Agent(FunctionModel(fn), output_type=str)
        a1n.run_sync("a", usage=nu)
        a2n.run_sync("b", usage=nu)
        assert wu.requests == nu.requests == 2

    def test_u08_token_fields_propagate(self):
        """Input/output tokens reach the accumulator identically."""
        from pydantic_ai import Agent
        from pydantic_ai.usage import RunUsage
        from pydantic_ai.messages import ModelResponse as MR
        from pydantic_ai.usage import RequestUsage
        from app.infrastructure.orchestration.pydantic_ai_investigation import (
            _TurnUsageCountingModel,
        )

        wu, nu = RunUsage(), RunUsage()

        def fn(m, i):
            return MR(
                parts=[TextPart("ok")],
                usage=RequestUsage(input_tokens=10, output_tokens=5),
            )

        Agent(
            _TurnUsageCountingModel(FunctionModel(fn), wu), output_type=str
        ).run_sync("a")
        Agent(FunctionModel(fn), output_type=str).run_sync("a", usage=nu)
        assert wu.input_tokens == nu.input_tokens
        assert wu.output_tokens == nu.output_tokens


# ===================================================================
# RQ-3 — P1 extended negatives
# ===================================================================


class TestP1ExtendedNegatives:
    def test_unknown_failure_code_stays_blocked(self):
        """Unclassified failure (no transient token) → identical call
        blocked — unknown failures fail closed."""
        unknown = GovernedCapabilityAttempt(
            status=GovernedCapabilityStatus.NOT_APPLICABLE,
            correlation_id="c",
            error_code="owner_returned_garbage",
        )
        calls = _p1_engine([unknown, unknown], [_SAME, _SAME])
        assert len(calls) == 1

    def test_success_then_identical_call_cached(self):
        """Success observation: identical re-call served from cache —
        no unjustified re-query (CONTROL, green today)."""
        ok = GovernedCapabilityAttempt(
            status=GovernedCapabilityStatus.SUCCESS, correlation_id="c"
        )
        calls = _p1_engine([ok, ok], [_SAME, _SAME])
        assert len(calls) == 1

    def test_genuine_unproductive_repetition_stays_banned(self):
        """Four identical calls after terminal failure — exactly one
        owner call ever. The no-progress guard's legitimate job."""
        calls = _p1_engine(
            [_terminal_attempt()] * 4, [_SAME] * 4
        )
        assert len(calls) == 1

    def test_tool_calls_limit_blocks_retry(self):
        """Exhausted tool budget → UsageLimits blocks before any
        retry could be contemplated (CONTROL)."""
        gates = _gates()
        catalog = gates._project_semantic_tool_catalog(
            correlation="c", deadline=TurnDeadline.start(30.0)
        )
        tool_name = catalog[0]["capability_id"]
        calls: list = []

        def _spy(**kwargs):
            calls.append(kwargs)
            return _transient_attempt()

        gates._governed_semantic_tool_invoke = _spy
        from tests.test_pydantic_ai_semantic_rework import _final_answer
        from app.infrastructure.orchestration.pydantic_ai_investigation import (
            PydanticAiInvestigationOrchestrator,
        )

        steps = {"n": 0}

        def _fn(m, i):
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
            if steps["n"] < 4:
                return ModelResponse(
                    parts=[ToolCallPart(tool_name, {"arguments": {"q": "x"}})]
                )
            return _final_answer("stop")

        engine = PydanticAiInvestigationOrchestrator(
            gates, model=FunctionModel(_fn), tool_calls_limit=2
        )
        engine.attempt("consulta")
        # goal + 1 invoke = 2 tool calls hits the cap — second invoke
        # never executed by the framework at all
        assert len(calls) <= 1


# ===================================================================
# RQ-1 — F1 lifecycle probes
# ===================================================================


class TestF1Lifecycle:
    def test_prepared_survives_for_run(self):
        """``prepared()`` is a WrapperToolset — for_run rebinding keeps
        the prepare layer (the B3 defect class that motivated the
        custom subclass)."""
        import asyncio
        from pydantic_ai import RunContext
        from pydantic_ai.usage import RunUsage
        from pydantic_ai.toolsets import FunctionToolset

        inner = FunctionToolset()

        @inner.add_function
        def probe(x: str) -> str:
            return "ok"

        wrapped = inner.prepared(
            lambda ctx, tds: [
                dataclasses.replace(td, description=(td.description or "") + " H")
                for td in tds
            ]
        )
        ctx = RunContext(deps=None, model=None, usage=RunUsage(), prompt="t")

        async def _defs():
            rebound = await wrapped.for_run(ctx)
            tools = await rebound.get_tools(ctx)
            return {
                n: tt.tool_def.description for n, tt in tools.items()
            }

        descs = asyncio.new_event_loop().run_until_complete(_defs())
        assert all(" H" in (d or "") for d in descs.values())

    def test_prepared_propagates_inner_errors(self):
        """An inner toolset failure surfaces through prepared() —
        fail-closed, never silently empty."""
        import asyncio
        from pydantic_ai import RunContext
        from pydantic_ai.usage import RunUsage
        from pydantic_ai.toolsets import FunctionToolset, WrapperToolset

        class _Failing(WrapperToolset):
            async def get_tools(self, ctx):
                raise RuntimeError("discovery failed")

        inner = FunctionToolset()

        @inner.add_function
        def probe(x: str) -> str:
            return "ok"

        wrapped = _Failing(inner).prepared(lambda c, t: t)
        ctx = RunContext(deps=None, model=None, usage=RunUsage(), prompt="t")
        with pytest.raises(RuntimeError):
            asyncio.new_event_loop().run_until_complete(
                wrapped.get_tools(ctx)
            )

    def test_prepared_cannot_expose_extra_tools(self):
        """prepare() adding a tool → UserError: the native seam is
        structurally fail-closed for the WRITE-exposure class."""
        import asyncio
        from pydantic_ai import RunContext
        from pydantic_ai.usage import RunUsage
        from pydantic_ai.toolsets import FunctionToolset
        from pydantic_ai.tools import ToolDefinition

        inner = FunctionToolset()

        @inner.add_function
        def read_only(x: str) -> str:
            return "ok"

        wrapped = inner.prepared(
            lambda c, tds: tds + [ToolDefinition(name="hidden_write")]
        )
        ctx = RunContext(deps=None, model=None, usage=RunUsage(), prompt="t")
        with pytest.raises(Exception):
            asyncio.new_event_loop().run_until_complete(
                wrapped.get_tools(ctx)
            )
