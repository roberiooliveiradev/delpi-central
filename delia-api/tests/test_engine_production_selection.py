"""Doc 231 — production engine selection after LangGraph retirement.

``DELIA_ORCHESTRATION_ENGINE`` selects ``pydantic_ai`` (default) or
``delia`` (Application sequencer rollback). LangGraph identifiers and
retired fan-out/checkpoint flags fail closed.
"""

from __future__ import annotations

import pytest

from app.composition.root_composer import (
    _resolve_orchestration_attempt,
    _SUPPORTED_ORCHESTRATION_ENGINES,
)
from tests.support.capability_fixtures import (
    _providers,
)
from tests.support.capability_fixtures import (
    FakeProposalModel as RelevanceProposalModel,
)


def _gates():
    from app.application.capability_provision.orchestration import (
        OperationalCapabilityOrchestrator,
    )
    from app.application.model_invocation.invoke_model import InvokeModel
    from tests.support.capability_fixtures import (
        load_test_orchestration_instructions,
    )

    return OperationalCapabilityOrchestrator(
        _providers(),
        orchestration_instructions=load_test_orchestration_instructions(),
        invoke_model=InvokeModel(RelevanceProposalModel(())),
    )


def _test_model():
    from pydantic_ai.models.test import TestModel

    return TestModel()


class TestSelection:
    def test_default_supported_engines(self):
        assert _SUPPORTED_ORCHESTRATION_ENGINES == frozenset(
            {"pydantic_ai"}
        )
        assert "langgraph" not in _SUPPORTED_ORCHESTRATION_ENGINES

    def test_pydantic_ai_selects_investigation_runtime(self):
        from app.infrastructure.orchestration.pydantic_ai_investigation import (
            PydanticAiInvestigationOrchestrator,
        )

        attempt = _resolve_orchestration_attempt(
            "pydantic_ai", _gates(), investigation_model=_test_model()
        )
        assert isinstance(attempt, PydanticAiInvestigationOrchestrator)
        assert callable(getattr(attempt, "attempt", None))

    def test_delia_rollback_retired_and_rejected(self):
        # The `delia` Application-sequencer rollback is retired — its
        # semantic engine was removed; the identifier fails closed.
        with pytest.raises(ValueError):
            _resolve_orchestration_attempt("delia", _gates())

    def test_langgraph_rejected(self):
        for bogus in ("langgraph", "langgraph_b0", "LANGGRAPH"):
            with pytest.raises(ValueError):
                _resolve_orchestration_attempt(bogus, _gates())

    def test_invalid_config_fails_closed(self):
        for bogus in ("", "auto", "0", "delia "):
            with pytest.raises(ValueError):
                _resolve_orchestration_attempt(bogus, _gates())

    def test_retired_fanout_flag_fails_closed(self):
        with pytest.raises(ValueError, match="FANOUT"):
            _resolve_orchestration_attempt(
                "pydantic_ai",
                _gates(),
                investigation_model=_test_model(),
                subobjective_fanout_enabled=True,
            )

    def test_retired_checkpoint_path_fails_closed(self):
        with pytest.raises(ValueError, match="CHECKPOINT"):
            _resolve_orchestration_attempt(
                "pydantic_ai",
                _gates(),
                investigation_model=_test_model(),
                checkpoint_db_path="/tmp/retired.sqlite",
            )

    def test_pydantic_ai_requires_model(self):
        with pytest.raises(ValueError, match="model"):
            _resolve_orchestration_attempt("pydantic_ai", _gates())


class TestUntrustedSurfaces:
    def test_resolver_signature_has_no_request_path(self):
        import inspect

        params = list(
            inspect.signature(_resolve_orchestration_attempt).parameters
        )
        assert params == [
            "engine_name",
            "gates",
            "investigation_model",
            "investigation_model_factory",
            "subobjective_fanout_enabled",
            "checkpoint_db_path",
            "request_limit",
            "tool_calls_limit",
            "agent_retries",
            "tool_projection_limit",
            "prior_turns_limit",
            "context_window_tokens",
        ]
