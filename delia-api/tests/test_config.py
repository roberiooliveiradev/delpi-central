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


def test_llm_tuning_comes_from_runtime_json(monkeypatch):
    # Doc 243: intelligence tunables resolve from the single JSON
    # artifact — retired env values fail closed (covered by
    # test_pydantic_ai_runtime_config).
    settings = Settings()
    assert settings.llm_max_output_tokens is None
    assert settings.model_stage_timeout_seconds == 60.0
    assert settings.llm_call_max_attempts == 3


def test_no_direct_delpi_openapi_settings(monkeypatch):
    """Task DELIA-C3-REMOVE-DIRECT-DELPI-BOUNDARY-AND-DEPLOY-01: the
    direct DELPI OpenAPI source is removed — its exclusive env surface
    must not exist on Settings."""
    monkeypatch.setenv("DELIA_OPENAPI_DELPI_ENABLED", "true")
    monkeypatch.setenv("DELIA_OPENAPI_DELPI_BASE_URL", "http://x:1")
    monkeypatch.setenv(
        "DELIA_OPENAPI_DELPI_DECLARATIONS_PATH", "/tmp/x.json"
    )
    settings = Settings()
    assert not hasattr(settings, "openapi_delpi_enabled")
    assert not hasattr(settings, "openapi_delpi_base_url")
    assert not hasattr(settings, "openapi_delpi_declarations_path")
