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
