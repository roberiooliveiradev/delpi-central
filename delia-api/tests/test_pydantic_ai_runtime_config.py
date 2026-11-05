"""Doc 243 — unified non-secret Pydantic AI runtime configuration.

One checked-in JSON artifact is the single declarative source of every
non-secret intelligence tunable. Legacy model-runtime selection is
removed; migrated environment variables fail closed; the validated
snapshot reaches the Agent, UsageLimits, budgets and tool projection.
"""

from __future__ import annotations

import importlib.util
import inspect
import json
from pathlib import Path

import pytest

from app.infrastructure.config.pydantic_ai_runtime_config import (
    PydanticAiRuntimeConfigError,
    load_pydantic_ai_runtime_config,
)
from app.infrastructure.config.settings import Settings

_CONFIG_PATH = (
    Path(__file__).resolve().parents[1]
    / "config"
    / "pydantic_ai.runtime.delpi.json"
)


def _document() -> dict:
    return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))


def _write(tmp_path: Path, doc: dict) -> Path:
    target = tmp_path / "runtime.json"
    target.write_text(json.dumps(doc), encoding="utf-8")
    return target


# ---------- document contract ----------

def test_checked_in_document_loads_default_profile():
    config = load_pydantic_ai_runtime_config(_CONFIG_PATH)
    assert config.schema_version == 1
    assert config.profile_name == "local_ollama"
    assert config.profile.model.provider == "openai_compatible"
    assert config.profile.model.model_name == (
        "qwen3:4b-instruct-2507-q4_K_M"
    )
    assert config.fingerprint


def test_profile_selector_resolves_named_profile():
    config = load_pydantic_ai_runtime_config(
        _CONFIG_PATH, profile_selector="openrouter_kimi"
    )
    assert config.profile_name == "openrouter_kimi"
    assert config.profile.model.model_name == "moonshotai/kimi-k3"
    assert config.profile.generation.max_output_tokens == 2048
    assert config.profile.budgets.max_governed_attempts == 1


def test_unknown_profile_selector_fails_closed(tmp_path):
    with pytest.raises(PydanticAiRuntimeConfigError):
        load_pydantic_ai_runtime_config(
            _CONFIG_PATH, profile_selector="no_such_profile"
        )


def test_fingerprint_is_profile_sensitive_and_non_secret():
    base = load_pydantic_ai_runtime_config(_CONFIG_PATH)
    other = load_pydantic_ai_runtime_config(
        _CONFIG_PATH, profile_selector="openrouter_kimi"
    )
    assert base.fingerprint != other.fingerprint
    for token in ("key", "secret", "token", "password"):
        assert token not in base.fingerprint


def test_malformed_json_fails_closed(tmp_path):
    target = tmp_path / "bad.json"
    target.write_text("{not json", encoding="utf-8")
    with pytest.raises(PydanticAiRuntimeConfigError):
        load_pydantic_ai_runtime_config(target)


def test_missing_file_fails_closed(tmp_path):
    with pytest.raises(PydanticAiRuntimeConfigError):
        load_pydantic_ai_runtime_config(tmp_path / "absent.json")


@pytest.mark.parametrize(
    "mutation",
    [
        lambda doc: doc.update({"unknown_top": True}),
        lambda doc: doc.update({"schema_version": 99}),
        lambda doc: doc.update({"kind": "other_kind"}),
        lambda doc: doc.update({"resource_id": "other.id"}),
        lambda doc: doc["profiles"]["local_ollama"].update(
            {"unknown_section": {}}
        ),
        lambda doc: doc["profiles"]["local_ollama"]["agent"].update(
            {"unknown_key": 1}
        ),
        lambda doc: doc["profiles"]["local_ollama"]["agent"].update(
            {"request_limit": 0}
        ),
        lambda doc: doc["profiles"]["local_ollama"]["agent"].update(
            {"request_limit": "twelve"}
        ),
        lambda doc: doc["profiles"]["local_ollama"]["agent"].update(
            {"llm_call_max_attempts": 99}
        ),
        lambda doc: doc["profiles"]["local_ollama"]["agent"].update(
            {"retries": -1}
        ),
        lambda doc: doc["profiles"]["local_ollama"]["budgets"].update(
            {"turn_budget_seconds": -5}
        ),
        lambda doc: doc["profiles"]["local_ollama"]["budgets"].update(
            {"max_governed_attempts": 5}
        ),
        lambda doc: doc["profiles"]["local_ollama"]["tool_results"].update(
            {"max_projection_chars": 10}
        ),
        lambda doc: doc["profiles"]["local_ollama"]["model"].update(
            {"provider": "another_provider"}
        ),
        lambda doc: doc["profiles"]["local_ollama"]["model"].update(
            {"model_name": ""}
        ),
        lambda doc: doc["profiles"]["local_ollama"]["model"].update(
            {"api_key": "sk-should-never-load"}
        ),
        lambda doc: doc["profiles"]["local_ollama"]["budgets"].update(
            {"turn_budget_seconds": 400.0}
        ),
        lambda doc: doc["profiles"]["local_ollama"]["budgets"].update(
            {"model_stage_timeout_seconds": 400.0}
        ),
        lambda doc: doc.update({"default_profile": "missing"}),
        lambda doc: doc.update({"profiles": {}}),
        lambda doc: doc["profiles"]["local_ollama"].pop("budgets"),
        lambda doc: doc["profiles"]["local_ollama"]["observability"].update(
            {"record_usage": "yes"}
        ),
    ],
    ids=[
        "unknown_top_key",
        "bad_schema_version",
        "bad_kind",
        "bad_resource_id",
        "unknown_section",
        "unknown_agent_key",
        "request_limit_zero",
        "request_limit_not_int",
        "llm_call_attempts_above_ceiling",
        "retries_negative",
        "turn_budget_negative",
        "governed_attempts_above_ceiling",
        "projection_chars_too_small",
        "unsupported_provider",
        "empty_model_name",
        "secret_field_rejected",
        "turn_above_interaction_total",
        "stage_timeout_above_turn",
        "default_profile_missing",
        "profiles_empty",
        "missing_budgets_section",
        "observability_not_bool",
    ],
)
def test_invalid_documents_fail_closed(tmp_path, mutation):
    doc = _document()
    mutation(doc)
    target = _write(tmp_path, doc)
    with pytest.raises(PydanticAiRuntimeConfigError):
        load_pydantic_ai_runtime_config(target)


def test_secret_fields_rejected_at_any_depth(tmp_path):
    doc = _document()
    doc["profiles"]["local_ollama"]["context"]["nested"] = {
        "client_secret": "abc"
    }
    with pytest.raises(PydanticAiRuntimeConfigError):
        load_pydantic_ai_runtime_config(_write(tmp_path, doc))


# ---------- settings consumes the snapshot ----------

def test_settings_resolves_checked_in_profile(monkeypatch):
    monkeypatch.delenv("DELIA_RUNTIME_PROFILE", raising=False)
    settings = Settings()
    assert settings.llm_model == "qwen3:4b-instruct-2507-q4_K_M"
    assert settings.llm_provider == "openai_compatible"
    assert settings.llm_timeout_seconds == 60.0
    assert settings.llm_max_output_tokens is None
    assert settings.llm_context_tokens == 4096
    assert settings.model_stage_timeout_seconds == 60.0
    assert settings.turn_budget_seconds == 300.0
    assert settings.interaction_total_budget_seconds == 300.0
    assert settings.max_governed_attempts == 2
    assert settings.llm_call_max_attempts == 3
    assert settings.interaction_call_timeout_seconds == 30.0
    assert settings.agent_request_limit == 12
    assert settings.agent_tool_calls_limit == 8
    assert settings.agent_retries == 1
    assert settings.tool_result_max_projection_chars == 6000
    assert settings.runtime_profile == "local_ollama"
    assert settings.runtime_config_fingerprint


def test_settings_profile_selector_env(monkeypatch):
    monkeypatch.setenv("DELIA_RUNTIME_PROFILE", "openrouter_kimi")
    settings = Settings()
    assert settings.runtime_profile == "openrouter_kimi"
    assert settings.llm_model == "moonshotai/kimi-k3"
    assert settings.llm_max_output_tokens == 2048
    assert settings.max_governed_attempts == 1


def test_settings_unknown_profile_env_fails_closed(monkeypatch):
    monkeypatch.setenv("DELIA_RUNTIME_PROFILE", "bogus")
    with pytest.raises(PydanticAiRuntimeConfigError):
        Settings()


def test_llm_secret_bindings_stay_environment(monkeypatch):
    monkeypatch.setenv("DELIA_LLM_BASE_URL", "http://ollama:11434/v1")
    monkeypatch.setenv("DELIA_LLM_API_KEY", "local-dev")
    settings = Settings()
    assert settings.llm_base_url == "http://ollama:11434/v1"
    assert settings.llm_api_key == "local-dev"


# ---------- retired environment fails closed ----------

@pytest.mark.parametrize(
    "name",
    [
        "DELIA_LLM_PROVIDER",
        "DELIA_LLM_MODEL",
        "DELIA_LLM_TIMEOUT_SECONDS",
        "DELIA_LLM_MAX_OUTPUT_TOKENS",
        "DELIA_LLM_CONTEXT_TOKENS",
        "DELIA_MODEL_STAGE_TIMEOUT_SECONDS",
        "DELIA_TURN_BUDGET_SECONDS",
        "DELIA_INTERACTION_TOTAL_BUDGET_SECONDS",
        "DELIA_MAX_GOVERNED_ATTEMPTS",
        "DELIA_LLM_CALL_MAX_ATTEMPTS",
    ],
)
def test_migrated_env_values_fail_closed(monkeypatch, name):
    monkeypatch.setenv(name, "1")
    with pytest.raises(ValueError, match=name):
        Settings()


@pytest.mark.parametrize(
    "name",
    [
        "DELIA_LLM_PROVIDER",
        "DELIA_LLM_MODEL",
        "DELIA_LLM_TIMEOUT_SECONDS",
        "DELIA_TURN_BUDGET_SECONDS",
    ],
)
def test_empty_migrated_env_values_are_harmless(monkeypatch, name):
    monkeypatch.setenv(name, "")
    assert Settings() is not None


def test_legacy_model_runtime_fails_closed(monkeypatch):
    monkeypatch.setenv("DELIA_MODEL_RUNTIME", "legacy")
    with pytest.raises(ValueError, match="DELIA_MODEL_RUNTIME"):
        Settings()


def test_unknown_model_runtime_fails_closed(monkeypatch):
    monkeypatch.setenv("DELIA_MODEL_RUNTIME", "langgraph")
    with pytest.raises(ValueError, match="DELIA_MODEL_RUNTIME"):
        Settings()


def test_explicit_pydantic_ai_model_runtime_is_noop(monkeypatch):
    monkeypatch.setenv("DELIA_MODEL_RUNTIME", "pydantic_ai")
    assert Settings() is not None


def test_model_runtime_attribute_removed():
    assert not hasattr(Settings(), "model_runtime")


# ---------- wiring: snapshot reaches the runtime ----------

def test_composer_maps_snapshot_to_investigation_kwargs(monkeypatch):
    monkeypatch.delenv("DELIA_RUNTIME_PROFILE", raising=False)
    from app.composition.root_composer import (
        _investigation_runtime_kwargs,
    )

    kwargs = _investigation_runtime_kwargs(Settings())
    assert kwargs["request_limit"] == 12
    assert kwargs["tool_calls_limit"] == 8
    assert kwargs["agent_retries"] == 1
    assert kwargs["tool_projection_limit"] == 6000
    assert kwargs["prior_turns_limit"] == 4


def test_resolve_orchestration_attempt_forwards_limits():
    from pydantic_ai.models.test import TestModel

    from app.composition.root_composer import (
        _resolve_orchestration_attempt,
    )
    from tests.support.capability_fixtures import _providers
    from tests.support.capability_fixtures import (
        FakeProposalModel,
        load_test_orchestration_instructions,
    )
    from app.application.capability_provision.orchestration import (
        OperationalCapabilityOrchestrator,
    )
    from app.application.model_invocation.invoke_model import InvokeModel

    gates = OperationalCapabilityOrchestrator(
        _providers(),
        orchestration_instructions=load_test_orchestration_instructions(),
        invoke_model=InvokeModel(FakeProposalModel(())),
    )
    orchestrator = _resolve_orchestration_attempt(
        "pydantic_ai",
        gates,
        investigation_model=TestModel(),
        request_limit=5,
        tool_calls_limit=3,
        agent_retries=2,
        tool_projection_limit=1234,
        prior_turns_limit=2,
    )
    assert orchestrator._request_limit == 5
    assert orchestrator._tool_calls_limit == 3
    assert orchestrator._agent_retries == 2
    assert orchestrator._tool_projection_limit == 1234
    assert orchestrator._prior_turns_limit == 2


def test_json_change_changes_effective_limits(tmp_path):
    """The JSON artifact drives the runtime — not a parsed-only dict."""
    doc = _document()
    doc["profiles"]["local_ollama"]["agent"]["request_limit"] = 4
    doc["profiles"]["local_ollama"]["agent"]["tool_calls_limit"] = 2
    doc["profiles"]["local_ollama"]["tool_results"][
        "max_projection_chars"
    ] = 1500
    config = load_pydantic_ai_runtime_config(_write(tmp_path, doc))
    assert config.profile.agent.request_limit == 4
    assert config.profile.agent.tool_calls_limit == 2
    assert config.profile.tool_results.max_projection_chars == 1500


# ---------- zero legacy ----------

def test_legacy_model_invocation_adapter_removed():
    assert (
        importlib.util.find_spec(
            "app.infrastructure.model_invocation.openai_compatible_adapter"
        )
        is None
    )


def test_composer_has_no_legacy_branch():
    from app.composition import root_composer

    source = inspect.getsource(root_composer._wire_real_provider_handler)
    assert "legacy" not in source
    assert "OpenAICompatibleModelInvocationAdapter" not in source
