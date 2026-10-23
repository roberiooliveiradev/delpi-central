from app.infrastructure.config.settings import Settings


def test_default_settings_are_safe_and_explicit(monkeypatch):
    monkeypatch.delenv("DELIA_DEBUG", raising=False)
    monkeypatch.delenv("SERVICE_NAME", raising=False)
    monkeypatch.delenv("SERVICE_VERSION", raising=False)
    settings = Settings()
    assert settings.service_name == "delia-api"
    assert settings.debug is False
    assert settings.service_version == "0.0.1"


def test_debug_requires_explicit_flag(monkeypatch):
    monkeypatch.setenv("DELIA_DEBUG", "true")
    settings = Settings()
    assert settings.debug is True


def test_testing_settings_disable_debug(monkeypatch):
    monkeypatch.setenv("DELIA_DEBUG", "true")
    settings = Settings.for_testing()
    assert settings.environment == "testing"
    assert settings.debug is False


def test_llm_max_output_tokens_defaults_to_unset(monkeypatch):
    monkeypatch.delenv("DELIA_LLM_MAX_OUTPUT_TOKENS", raising=False)
    assert Settings().llm_max_output_tokens is None


def test_llm_max_output_tokens_parses_env(monkeypatch):
    monkeypatch.setenv("DELIA_LLM_MAX_OUTPUT_TOKENS", "2048")
    assert Settings().llm_max_output_tokens == 2048


def test_model_stage_timeout_defaults_to_bounded_cap(monkeypatch):
    # Doc 103: the approved per-LLM-call budget is 60s.
    monkeypatch.delenv("DELIA_MODEL_STAGE_TIMEOUT_SECONDS", raising=False)
    assert Settings().model_stage_timeout_seconds == 60.0


def test_model_stage_timeout_parses_env(monkeypatch):
    monkeypatch.setenv("DELIA_MODEL_STAGE_TIMEOUT_SECONDS", "30")
    assert Settings().model_stage_timeout_seconds == 30.0


def test_llm_call_max_attempts_defaults_to_off(monkeypatch):
    # Doc 103 GATE 1: absent config fails closed to 1 — production
    # never retries a logical LLM call involuntarily.
    monkeypatch.delenv("DELIA_LLM_CALL_MAX_ATTEMPTS", raising=False)
    settings = Settings()
    assert settings.llm_call_max_attempts == 1
    assert settings.llm_call_max_attempts_config_source == "default"
    assert settings.llm_call_max_attempts_config_invalid is False


def test_llm_call_max_attempts_accepts_approved_range(monkeypatch):
    for raw, expected in (("1", 1), ("2", 2), ("3", 3)):
        monkeypatch.setenv("DELIA_LLM_CALL_MAX_ATTEMPTS", raw)
        settings = Settings()
        assert settings.llm_call_max_attempts == expected
        assert settings.llm_call_max_attempts_config_source == (
            "environment"
        )
        assert settings.llm_call_max_attempts_config_invalid is False


def test_llm_call_max_attempts_invalid_values_fail_closed(monkeypatch):
    # Zero, negative, above the PO-approved ceiling, non-numeric and
    # empty all resolve to 1 (OFF) and are flagged invalid — never an
    # involuntary retry enablement.
    for raw in ("0", "-1", "4", "99", "abc", "", "  "):
        monkeypatch.setenv("DELIA_LLM_CALL_MAX_ATTEMPTS", raw)
        settings = Settings()
        assert settings.llm_call_max_attempts == 1
        assert settings.llm_call_max_attempts_config_invalid is True
