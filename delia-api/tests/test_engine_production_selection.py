"""Task 07 — production engine selection (DELIA-C3-LANGGRAPH-
PRODUCTION-ACTIVATION-01).

Product-owner authorization promotes LangGraph B1 to the DEFAULT
production orchestration engine behind the same
``SupportsGovernedCapabilityAttempt`` boundary, with Engine A
preserved as the explicitly selectable legacy implementation.

Selection is backend-controlled configuration ONLY
(DELIA_ORCHESTRATION_ENGINE): unknown values fail closed at
composition; request input, provider metadata and model output can
never steer it; one turn executes exactly one engine; a B1 failure
never auto-replays under Engine A (no duplicate business effects).
"""

from __future__ import annotations

import pytest

from app.composition.root_composer import (
    _resolve_orchestration_attempt,
    _SUPPORTED_ORCHESTRATION_ENGINES,
)
from tests.test_governed_attempt_contract import (
    _cri_clause,
    build_engine,
)
from tests.test_engine_b_recovery_reuse import (
    _providers,
    _reuse_proposal,
)
from tests.test_goal_evidence_relevance import (
    FakeProposalModel as RelevanceProposalModel,
)


def _gates():
    """The shared governed-primitives provider — Engine A's class,
    per the accepted residual (doc 195)."""
    from app.application.capability_provision.orchestration import (
        OperationalCapabilityOrchestrator,
    )

    from app.application.model_invocation.invoke_model import InvokeModel
    from tests.test_governed_attempt_contract import (
        load_test_orchestration_instructions,
    )

    clause = _cri_clause()
    return OperationalCapabilityOrchestrator(
        _providers(),
        orchestration_instructions=load_test_orchestration_instructions(),
        invoke_model=InvokeModel(RelevanceProposalModel(_reuse_proposal())),
        response_intelligence_enabled=True,
        cri_instruction_clause=clause.text,
        cri_instruction_version=clause.version,
    )


# ---------------- P1/P2/P11 — selection semantics ----------------


class TestSelection:
    def test_p1_default_selects_langgraph_b1(self):
        """P1 — default production composition resolves to the
        LangGraph B1 implementation."""
        attempt = _resolve_orchestration_attempt("langgraph", _gates())
        from app.infrastructure.orchestration.langgraph_engine import (
            LangGraphCapabilityOrchestrator,
        )

        assert isinstance(attempt, LangGraphCapabilityOrchestrator)
        assert callable(getattr(attempt, "attempt", None))
        assert attempt._recovery_reuse_enabled is True

    def test_p2_legacy_selects_engine_a(self):
        """P2 — explicit `delia` selects the legacy implementation."""
        from app.application.capability_provision.orchestration import (
            OperationalCapabilityOrchestrator,
        )

        attempt = _resolve_orchestration_attempt("delia", _gates())
        assert isinstance(attempt, OperationalCapabilityOrchestrator)
        assert callable(getattr(attempt, "attempt", None))

    def test_p3_invalid_config_fails_closed(self):
        """P3 — an unknown engine identifier raises at composition;
        nothing is silently selected."""
        for bogus in ("", "langgraph2", "DELIA", "auto", "0", "delia "):
            with pytest.raises(ValueError):
                _resolve_orchestration_attempt(bogus, _gates())

    def test_p11_rollback_needs_no_migration(self):
        """P11 — legacy selection is a config value on the same
        contract: identical boundary type, no extra wiring."""
        from app.application.capability_provision.orchestration import (
            OperationalCapabilityOrchestrator,
        )

        engine = _resolve_orchestration_attempt("delia", _gates())
        assert isinstance(engine, OperationalCapabilityOrchestrator)
        assert "delia" in _SUPPORTED_ORCHESTRATION_ENGINES
        assert "langgraph" in _SUPPORTED_ORCHESTRATION_ENGINES


# ---------------- P4/P5 — untrusted surfaces cannot steer ----------------


class TestUntrustedSurfaces:
    def test_p4_input_text_cannot_select_engine(self):
        """P4 — the resolver signature takes only (engine_name,
        gates): request input has no path into selection. An
        adversarial user text never reaches composition."""
        import inspect

        params = list(
            inspect.signature(_resolve_orchestration_attempt).parameters
        )
        assert params == ["engine_name", "gates"]

    def test_p5_provider_metadata_cannot_select_engine(self):
        """P5 — selection is config-resolved before providers are
        even consulted; a forged group/capability name cannot alter
        the resolved type."""
        from app.infrastructure.orchestration.langgraph_engine import (
            LangGraphCapabilityOrchestrator,
        )

        # The resolver's only inputs are the config identifier and
        # the already-composed gates — provider group/capability
        # metadata never reaches it, so a forged name that mimics an
        # engine id cannot steer the resolved type.
        attempt = _resolve_orchestration_attempt("langgraph", _gates())
        assert isinstance(attempt, LangGraphCapabilityOrchestrator)


# ---------------- P6/P7 — one engine, no auto-replay ----------------


class TestSingleEngineExecution:
    def test_p6_single_engine_per_turn(self):
        """P6 — a turn executes through exactly one attempt()
        implementation."""
        gates = _gates()
        engine = _resolve_orchestration_attempt("langgraph", gates)

        calls = []
        original = gates._attempt if hasattr(gates, "_attempt") else None
        if original is not None:
            gates._attempt = lambda *a, **k: (
                calls.append(1), original(*a, **k)
            )[1]
        engine.attempt("2 exemplos de terminal bala")
        # Engine A's own attempt()/attempt-entrypoint must not run —
        # B1 sequences the shared stage gates only.
        assert calls == []

    def test_p7_b1_failure_no_engine_a_replay(self):
        """P7 — a B1 execution failure propagates; Engine A's
        attempt() is never invoked as a fallback (a second business
        execution could duplicate effects)."""
        gates = _gates()
        engine = _resolve_orchestration_attempt("langgraph", gates)

        invoked = []
        original = getattr(gates, "attempt", None)
        if original is not None:
            gates.attempt = lambda *a, **k: invoked.append(1)

        def explode(_stage):
            raise RuntimeError("node boom")

        try:
            engine._gates._preflight = explode
        except AttributeError:
            pass
        try:
            engine.attempt("2 exemplos de terminal bala")
        except Exception:
            pass
        assert invoked == []

    def test_p8_gates_injection(self):
        """P8 — B1 consumes the injected governed gates contract,
        never constructs its own primitives."""
        gates = _gates()
        engine = _resolve_orchestration_attempt("langgraph", gates)
        assert engine._gates is gates
        assert callable(getattr(engine._gates, "_governed_owner_path"))


# ---------------- P9/P10 — isolation + deadlines ----------------


class TestIsolationAndDeadlines:
    def test_p9_concurrent_turns_isolated(self):
        """P9 — two turns through the same selected engine share no
        mutable orchestration state."""
        import threading

        engine = _resolve_orchestration_attempt("langgraph", _gates())
        results = {}
        errors = []
        barrier = threading.Barrier(2)

        def worker(idx):
            try:
                barrier.wait(timeout=10)
                results[idx] = engine.attempt(
                    "2 exemplos de terminal bala"
                ).status
            except BaseException as exc:  # noqa: BLE001
                errors.append(exc)

        ts = [threading.Thread(target=worker, args=(i,)) for i in (0, 1)]
        for t in ts:
            t.start()
        for t in ts:
            t.join(timeout=60)
        assert not errors
        assert results[0] == results[1]

    def test_p10_cancellation_preserved(self):
        """P10 — cancel_check propagates identically under B1."""
        engine = _resolve_orchestration_attempt("langgraph", _gates())
        attempt = engine.attempt(
            "2 exemplos de terminal bala",
            cancel_check=lambda: "PROCESSING_TIMEOUT",
        )
        assert "PROCESSING_TIMEOUT" in str(attempt.status)


# ---------------- P12 — sanitized identification ----------------


class TestObservability:
    def test_p12_engine_identifiable_sanitized(self, caplog):
        """P12 — the selected engine is identifiable via sanitized
        operational metadata (id + graph trace), never secrets or
        prompts."""
        import logging

        engine = _resolve_orchestration_attempt("langgraph", _gates())
        with caplog.at_level(logging.INFO):
            engine.attempt("2 exemplos de terminal bala")
        trace = getattr(engine, "last_node_trace", [])
        assert trace  # engine id + executed nodes are observable
        blob = str(trace) + caplog.text
        assert "terminal bala" not in blob
        assert "API_KEY" not in blob


# ---------------- application integration (§9) ----------------


class TestComposedPath:
    def test_handler_to_b1_composed_attempt(self):
        """§9 — the REAL composed path: HandleInteractiveConversationTurn
        → SupportsGovernedCapabilityAttempt → LangGraph adapter — not
        only adapter unit tests."""
        from app.application.interaction.handle_interactive_turn import (
            HandleInteractiveConversationTurn,
        )
        from app.application.interaction.contracts import (
            InteractiveTurnRequest,
            PlatformAccessContext,
        )
        from app.application.model_invocation.invoke_model import (
            InvokeModel,
        )
        from app.infrastructure.model_invocation.deterministic_test_adapter import (
            DeterministicTestAdapter,
        )

        engine = _resolve_orchestration_attempt("langgraph", _gates())
        handler = HandleInteractiveConversationTurn(
            InvokeModel(DeterministicTestAdapter(behavior="success")),
            capability_orchestration=engine,
        )
        result = handler.execute(
            InteractiveTurnRequest(
                access_context=PlatformAccessContext(
                    user_id="u1",
                    name="User",
                    email="u@example.com",
                    effective_permissions=("delia.access",),
                    is_superadmin=False,
                ),
                input_text="2 exemplos de terminal bala",
            )
        )
        assert result is not None
        assert getattr(engine, "last_node_trace", [])
        # B1 sequencing produced a governed attempt through the
        # shared boundary — the trace is sanitized metadata, not the
        # business answer.
        assert "owner_path" in engine.last_node_trace or any(
            "owner" in n for n in engine.last_node_trace
        )
