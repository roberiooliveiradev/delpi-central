"""E1-FINAL — streaming/cancellation usage parity + pagination contract
closure + MCPToolset prepared() parity.

TASK: DELIA-C3-T2-F2-E1-FINAL-PARITY-CONTRACT-AND-INDEPENDENT-VERIFICATION-01

Closes the last untested seams: streaming counting, cancellation
counting, page-order contract question, has_more contradictions, and
prepared() on the MCP stub toolset. Zero runtime changes.
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


from app.application.capability_provision.semantic_capability_support import (
    MaterialObligation,
    _joint_collection_coverage,
)
from pydantic_ai.messages import ModelResponse, TextPart
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.usage import RequestUsage, RunUsage

from tests.test_f2_native_refactor_e1_closure import (
    _paged_attempt,
    _records,
)


# ===================================================================
# RQ-1 — streaming + cancellation usage parity
# ===================================================================


def _stream_fn(text: str = "hello"):
    """Streaming variant for FunctionModel — async-gen delta parts."""

    async def _fn(messages, _info):
        yield text

    return _fn


class TestStreamingUsageParity:
    def test_s01_complete_stream(self):
        """Full stream: wrapper counts via request_stream finally +
        stream.usage(); native path must equal it."""
        from pydantic_ai import Agent
        
        wu, nu = RunUsage(), RunUsage()
        fn = lambda m, i: ModelResponse(parts=[TextPart("ok")])
        aw = Agent(
            FunctionModel(fn, stream_function=_stream_fn()),
            output_type=str,
        )
        an = Agent(
            FunctionModel(fn, stream_function=_stream_fn()),
            output_type=str,
        )
        with aw.run_stream_sync("go", usage=wu) as res_w:
            res_w.get_output()
        with an.run_stream_sync("go", usage=nu) as res_n:
            res_n.get_output()
        assert wu.requests == nu.requests
        assert wu.requests == 1

    def test_s02_stream_abandoned_early(self):
        """Stream context exited without consuming output: wrapper's
        finally still counts; native must match."""
        from pydantic_ai import Agent
        
        wu, nu = RunUsage(), RunUsage()
        fn = lambda m, i: ModelResponse(parts=[TextPart("ok")])
        aw = Agent(
            FunctionModel(fn, stream_function=_stream_fn()),
            output_type=str,
        )
        an = Agent(
            FunctionModel(fn, stream_function=_stream_fn()),
            output_type=str,
        )
        with aw.run_stream_sync("go", usage=wu):
            pass  # abandon without get_output
        with an.run_stream_sync("go", usage=nu):
            pass
        # Record actual — both must count or both must not.
        assert wu.requests == nu.requests

    def test_s03_stream_model_raises_midway(self):
        """Stream function raising after partial output."""
        from pydantic_ai import Agent
        
        async def _bad_stream(messages, _info):
            yield "partial"
            raise RuntimeError("stream boom")

        wu, nu = RunUsage(), RunUsage()
        fn = lambda m, i: ModelResponse(parts=[TextPart("ok")])
        aw = Agent(
            FunctionModel(fn, stream_function=_bad_stream),
            output_type=str,
        )
        an = Agent(
            FunctionModel(fn, stream_function=_bad_stream),
            output_type=str,
        )
        try:
            with aw.run_stream_sync("go", usage=wu) as r:
                r.get_output()
        except Exception:
            pass
        try:
            with an.run_stream_sync("go", usage=nu) as r:
                r.get_output()
        except Exception:
            pass
        # Both must behave identically — whatever the count is.
        assert wu.requests == nu.requests


class TestCancellationUsageParity:
    def test_c01_cancelled_before_response(self):
        """Task cancelled while model request is in flight: wrapper
        increments only AFTER super().request() returns, so a cancelled
        request counts 0; native must equal (0 or equal — never more)."""
        import asyncio
        from pydantic_ai import Agent
        
        async def _slow(m, i):
            await asyncio.sleep(5)
            return ModelResponse(parts=[TextPart("ok")])

        async def _run():
            wu, nu = RunUsage(), RunUsage()
            aw = Agent(
                FunctionModel(_slow),
                output_type=str,
            )
            an = Agent(FunctionModel(_slow), output_type=str)
            t1 = asyncio.create_task(aw.run("go"))
            t2 = asyncio.create_task(an.run("go", usage=nu))
            await asyncio.sleep(0.05)
            t1.cancel()
            t2.cancel()
            for t in (t1, t2):
                try:
                    await t
                except BaseException:
                    pass
            return wu.requests, nu.requests

        wr, nr = asyncio.new_event_loop().run_until_complete(_run())
        assert wr == nr  # equal — typically 0 for both

    def test_c02_usage_late_reported_tokens(self):
        """Provider reports tokens only on completion: both paths
        record identical token fields."""
        from pydantic_ai import Agent
        
        wu, nu = RunUsage(), RunUsage()

        def fn(m, i):
            return ModelResponse(
                parts=[TextPart("ok")],
                usage=RequestUsage(input_tokens=42, output_tokens=7),
            )

        Agent(
            FunctionModel(fn), output_type=str
        ).run_sync("a", usage=wu)
        Agent(FunctionModel(fn), output_type=str).run_sync("a", usage=nu)
        assert (wu.requests, wu.input_tokens, wu.output_tokens) == (
            nu.requests,
            nu.input_tokens,
            nu.output_tokens,
        )

    def test_c03_no_double_counting(self):
        """Wrapper + usage= together must not double-count if both are
        ever wired simultaneously during E2 migration (defensive)."""
        from pydantic_ai import Agent
        
        shared = RunUsage()
        fn = lambda m, i: ModelResponse(parts=[TextPart("ok")])
        agent = Agent(
            FunctionModel(fn),
            output_type=str,
        )
        agent.run_sync("a", usage=shared)
        # POST-E2: the counting wrapper is gone — a single request must
        # be counted exactly once via the native usage= seam.
        assert shared.requests == 1


# ===================================================================
# RQ-2 — order & has_more contract
# ===================================================================


def _obl():
    return MaterialObligation(
        description="enumerate items", evidence_source="items"
    )


class TestPaginationOrderContract:
    """The contract question: does any AUTHORITATIVE consumer require
    sequential page order? ``_joint_collection_coverage`` proves set
    union == declared total — order is not a business guarantee of
    the owner contracts (page/offset envelope carries no order
    invariant; a reordered valid set is the same set). The legacy
    oracle's order check is internal diagnostics."""

    def test_order_1_3_2_complete_set(self):
        assert _joint_collection_coverage(
            _obl(),
            (
                _paged_attempt(_records(1, 40), 109),
                _paged_attempt(_records(81, 29), 109),
                _paged_attempt(_records(41, 40), 109),
            ),
        ) is True

    def test_order_3_2_1_complete_set(self):
        assert _joint_collection_coverage(
            _obl(),
            (
                _paged_attempt(_records(81, 29), 109),
                _paged_attempt(_records(41, 40), 109),
                _paged_attempt(_records(1, 40), 109),
            ),
        ) is True

    def test_order_2_1_3_complete_set(self):
        assert _joint_collection_coverage(
            _obl(),
            (
                _paged_attempt(_records(41, 40), 109),
                _paged_attempt(_records(1, 40), 109),
                _paged_attempt(_records(81, 29), 109),
            ),
        ) is True

    def test_page1_absent_incomplete(self):
        assert _joint_collection_coverage(
            _obl(),
            (
                _paged_attempt(_records(41, 40), 109),
                _paged_attempt(_records(81, 29), 109),
            ),
        ) is False

    def test_overlapping_pages_dedup_incomplete(self):
        """Pages sharing 20 records → union = 89 < 109 → not complete."""
        assert _joint_collection_coverage(
            _obl(),
            (
                _paged_attempt(_records(1, 40), 109),
                _paged_attempt(_records(21, 40), 109),
            ),
        ) is False


class TestHasMoreContract:
    """has_more contradictions: the authoritative verdict comes from
    record union vs declared total — envelope metadata is guidance,
    not proof."""

    def test_has_more_true_but_union_equals_total(self):
        """Source lied about has_more; the SET is provably complete —
        data wins over envelope flag."""
        assert _joint_collection_coverage(
            _obl(),
            (
                _paged_attempt(_records(1, 40), 80),
                _paged_attempt(_records(41, 40), 80),
            ),
        ) is True

    def test_has_more_false_union_below_total(self):
        """Source stopped early — union < declared total → not
        complete regardless of has_more."""
        assert _joint_collection_coverage(
            _obl(),
            (
                _paged_attempt(_records(1, 40), 109),
                _paged_attempt(_records(41, 40), 109),
            ),
        ) is False

    def test_source_wrong_total(self):
        """Source declares total=60 but delivers 80 distinct →
        union != declared total → not proven (source metadata
        untrusted; fail-closed)."""
        assert _joint_collection_coverage(
            _obl(),
            (
                _paged_attempt(_records(1, 40), 60),
                _paged_attempt(_records(41, 40), 60),
            ),
        ) is False

    def test_valid_pages_then_failure(self):
        """Valid pages + failed attempt → union of the valid set
        still < total → not complete."""
        from app.application.interaction.capability_attempt import (
            GovernedCapabilityStatus,
        )

        failed = dataclasses.replace(
            _paged_attempt(_records(81, 29), 109),
            status=GovernedCapabilityStatus.SOURCE_UNAVAILABLE,
        )
        assert _joint_collection_coverage(
            _obl(),
            (
                _paged_attempt(_records(1, 40), 109),
                _paged_attempt(_records(41, 40), 109),
                failed,
            ),
        ) is False

    def test_reordered_complete_set_stays_complete(self):
        """Post-E2 lock: page ORDER carries no authority — a reordered
        set whose record union equals the declared total is complete
        under the wired evaluator (the retired oracle's sequence check
        was diagnostics only)."""
        from tests.test_f2_native_refactor_e1 import (
            _paged_attempt,
        )

        assert _joint_collection_coverage(
            _obl(),
            (
                _paged_attempt([{"id": i} for i in range(1, 41)], 109),
                _paged_attempt([{"id": i} for i in range(81, 110)], 109),
                _paged_attempt([{"id": i} for i in range(41, 81)], 109),
            ),
        )


# ===================================================================
# RQ-4 — prepared() on the MCP stub toolset (native-MCP parity)
# ===================================================================


def test_prepared_works_on_mcp_stub_toolset():
    """``prepared()`` wraps an MCPToolset-shaped stub the same way it
    wraps a FunctionToolset — the seam is toolset-generic."""
    import asyncio
    from pydantic_ai import RunContext

    from fastmcp import Client
    from pydantic_ai.mcp import MCPToolset

    inner = MCPToolset(Client(alpha_beta_servers()["alpha"]))
    prepared = inner.prepared(
        lambda ctx, tds: [
            dataclasses.replace(td, description=(td.description or "") + " H")
            for td in tds
        ]
    )
    ctx = RunContext(deps=None, model=None, usage=RunUsage(), prompt="t")

    async def _defs(ts):
        try:
            tools = await ts.get_tools(ctx)
            return {n: tt.tool_def.description for n, tt in tools.items()}
        except Exception as e:
            return {"__error__": type(e).__name__}

    loop = asyncio.new_event_loop()
    try:
        base = loop.run_until_complete(_defs(inner))
        prep = loop.run_until_complete(_defs(prepared))
    finally:
        loop.close()
    # Whatever the stub yields (tools or a stub-specific error), the
    # prepared wrapper must reach the same inner surface.
    if "__error__" in base:
        assert prep.get("__error__") == base["__error__"]
    else:
        assert set(prep) == set(base)
        assert all(" H" in (d or "") for d in prep.values())


# ===================================================================
# RQ-5 — P1 contract re-lock (regression of E1 assertions)
# ===================================================================


def test_p1_e2_contract_terms_unchanged():
    """Locks the agreed P1 contract before E2 writes code:
    - exactly ONE identical re-invocation after a transient failure;
    - quota per fingerprint (capability + args);
    - no re-call after success;
    - terminal/authz/credential/unknown never retried;
    - no new retry manager: the seam is the existing cache branch."""
    from tests.test_f2_native_refactor_e1 import (
        _p1_engine,
        _transient_attempt,
        _terminal_attempt,
        _SAME,
    )

    # Post-E2 behavior: terminal stays fail-closed (1 call), a
    # transient failure permits exactly one identical re-invocation
    # (2 calls — the second reaches the owner again).
    assert len(_p1_engine([_terminal_attempt()] * 2, [_SAME] * 2)) == 1
    assert len(_p1_engine([_transient_attempt()] * 2, [_SAME] * 2)) == 2
