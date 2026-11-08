"""G7/doc 268 — behavioral composition regression: the governed
capability surface must be built when providers + valid instructions
exist, and must fail closed observably when they don't.

Guards the G3 regression where `load_orchestration_instructions` was
accidentally removed, silently disabling the whole capability path
(`surface=absent` with enabled providers).
"""

from __future__ import annotations

import dataclasses

from app.application.interaction.capability_attempt import (
    GovernedCapabilityAttempt,
    GovernedCapabilityStatus,
)
from app.application.interaction.instruction import (
    interaction_instruction_lineage,
)
from app.application.model_invocation.contracts import ModelRef
from app.application.model_invocation.invoke_model import InvokeModel
from app.domain.specialist_interop.model import SpecialistRef
from app.infrastructure.interoperability.config import (
    SpecialistConnectionProfile,
)
from app.infrastructure.model_invocation.deterministic_test_adapter import (
    DeterministicTestAdapter,
)
from app.composition import root_composer
from app.infrastructure.config.settings import Settings


def _settings() -> Settings:
    settings = Settings.for_testing()
    settings.mcp_specialist_enabled = {"pa": True}
    settings.mcp_specialist_endpoints = {"pa": "http://pa.test/mcp"}
    settings.orchestration_engine = "pydantic_ai"
    settings.llm_base_url = "http://ollama.test/v1"
    settings.llm_api_key = "test-key"
    settings.llm_model = "test-model"
    return settings


def _connections():
    return {
        "pa": SpecialistConnectionProfile(
            endpoint="http://pa.test/mcp",
            enabled=True,
            timeout_seconds=15.0,
            exchange_audience="pa",
            resource_audience="pa",
        )
    }


class _FakeInterop:
    """Interop stub — composition only needs the instance to exist;
    capability projection/invoke is exercised elsewhere."""

    def discover_catalog(self, specialist, request):
        raise AssertionError("composition test never discovers")


class _Adapter:
    def invoke(self, request):
        raise AssertionError("composition test never invokes")


def _handler(settings=None, connections=None):
    settings = settings or _settings()
    connections = _connections() if connections is None else connections
    return root_composer._compose_turn_handler(
        InvokeModel(DeterministicTestAdapter()),
        ModelRef(model_id="test", version="1", owner_ref="test"),
        _FakeInterop(),
        settings,
        connections,
    )


def test_composition_builds_governed_orchestration_with_valid_inputs():
    """Enabled specialist + valid instructions resource → the turn
    handler carries a non-null governed capability orchestration
    (surface=configured), never silently absent (doc 268 §2)."""
    handler = _handler()
    assert handler._capability_orchestration is not None


def test_composition_missing_instructions_fails_closed_observably():
    """Invalid/absent instructions resource → capability orchestration
    absent, but composition still starts (fail-closed) — the missing
    resource is logged as a config failure, NOT confused with absent
    business data (doc 268 §2)."""
    import app.composition.root_composer as rc

    def _boom(*a, **k):
        raise RuntimeError("resource_invalid")

    # The config failure is OBSERVABLE — never confused with absent
    # business data (doc 269 §2). A direct spy on the composer logger
    # is deterministic regardless of suite logging state.
    warnings: list[str] = []
    original_log = rc._logger.warning
    rc._logger.warning = lambda msg, *a, **k: warnings.append(msg)
    original = rc.load_orchestration_instructions
    rc.load_orchestration_instructions = _boom
    try:
        handler = _handler()
    finally:
        rc.load_orchestration_instructions = original
        rc._logger.warning = original_log
    assert handler is not None
    assert handler._capability_orchestration is None
    assert any(
        "delia_orchestration_instructions" in w and "fail_closed" in w
        for w in warnings
    )


def test_orchestration_instructions_resource_covers_required_keys():
    """The shipped resource satisfies every ORCHESTRATION_INSTRUCTION_KEYS
    required by the orchestrator — a regression guard that would have
    caught the G3 loader removal (doc 268 §3)."""
    import json
    from app.application.capability_provision.semantic_capability_support import (
    ORCHESTRATION_INSTRUCTION_KEYS,
)

    data = json.load(
        open("config/orchestration_instructions.delpi.json")
    )
    missing = set(ORCHESTRATION_INSTRUCTION_KEYS) - set(
        data["instructions"]
    )
    assert not missing


def test_runtime_profiles_share_execution_policy():
    """Unified model policy (DELIA-C3-UNIFIED-MODEL-RUNTIME): model
    profiles may differ ONLY in technical-capability fields —
    provider/model_name, context window, output budget. Execution
    policy (limits, retries, timeouts, governed attempts, history)
    must be identical across profiles so a model swap never changes
    investigation rules."""
    import json
    from pathlib import Path

    data = json.loads(
        Path("config/pydantic_ai.runtime.delpi.json").read_text()
    )
    technical = {
        ("model",), ("generation",), ("context", "effective_context_window_tokens"),
    }
    profiles = data["profiles"]
    assert len(profiles) >= 2

    def policy_fields(section, prefix=()):
        out = {}
        for k, v in section.items():
            path = prefix + (k,)
            if path in technical:
                continue
            out[path] = (
                policy_fields(v, path) if isinstance(v, dict) else v
            )
        return out

    flattened = {
        name: policy_fields(p) for name, p in profiles.items()
    }
    reference = flattened["local_ollama"]
    for name, fields in flattened.items():
        assert fields == reference, (
            f"profile {name} diverges in execution policy: "
            f"{set(fields.items()) ^ set(reference.items())}"
        )
