import importlib
import logging

import pytest

import engineering_app.config as config_module


@pytest.fixture(autouse=True)
def _restore_config():
    yield
    importlib.reload(config_module)


_CONFIG_ENV_KEYS = (
    "SERVICE_NAME",
    "ENGINEERING_API_ROOT_PATH",
    "PORT",
    "APP_ENV",
    "LOG_LEVEL",
    "KEYCLOAK_URL",
    "KEYCLOAK_REALM",
    "KEYCLOAK_JWKS_URL",
    "KEYCLOAK_ISSUER",
    "KEYCLOAK_AUDIENCE",
    "JWT_ALGORITHMS",
    "DELPI_AUTH_CORE_API_URL",
    "CORE_API_URL",
    "DELPI_AUTH_RBAC_TIMEOUT_SECONDS",
    "DELPI_AUTH_RBAC_CACHE_TTL_SECONDS",
    "DELPI_AUTH_RBAC_STALE_TTL_SECONDS",
)


def _reload_config(monkeypatch, **env):
    for key in _CONFIG_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    return importlib.reload(config_module)


def test_defaults(monkeypatch):
    module = _reload_config(monkeypatch)
    settings = module.Settings()
    assert settings.SERVICE_NAME == "engineering-api"
    assert settings.ENGINEERING_API_ROOT_PATH == "/apps/engineering-api"
    assert settings.PORT == "8000"
    assert settings.APP_ENV == "production"
    assert settings.LOG_LEVEL == "INFO"
    assert settings.resolved_log_level() == logging.INFO


def test_env_override(monkeypatch):
    module = _reload_config(
        monkeypatch,
        SERVICE_NAME="engineering-api-test",
        ENGINEERING_API_ROOT_PATH="/apps/engineering-api-dev",
        LOG_LEVEL="debug",
    )
    settings = module.Settings()
    assert settings.SERVICE_NAME == "engineering-api-test"
    assert settings.ENGINEERING_API_ROOT_PATH == "/apps/engineering-api-dev"
    assert settings.resolved_log_level() == logging.DEBUG


def test_invalid_log_level_falls_back_to_info(monkeypatch):
    module = _reload_config(monkeypatch, LOG_LEVEL="not-a-level")
    settings = module.Settings()
    assert settings.resolved_log_level() == logging.INFO


def test_settings_expose_no_secrets(monkeypatch):
    module = _reload_config(monkeypatch)
    public_attrs = [
        name
        for name in dir(module.Settings)
        if not name.startswith("_")
    ]
    # KEYCLOAK_* são URLs/realm/audience públicos — não segredos.
    for attr in public_attrs:
        lowered = attr.lower()
        assert "secret" not in lowered
        assert "password" not in lowered
        assert "token" not in lowered
        assert not lowered.endswith("_key")


def test_missing_auth_envs_reports_required(monkeypatch):
    module = _reload_config(monkeypatch)
    settings = module.Settings()
    assert settings.missing_auth_envs() == [
        "KEYCLOAK_ISSUER",
        "KEYCLOAK_AUDIENCE",
    ]

    monkeypatch.setenv("KEYCLOAK_ISSUER", "https://kc.test/realms/delpi")
    monkeypatch.setenv("KEYCLOAK_AUDIENCE", "delpi-central")
    assert settings.missing_auth_envs() == []


def test_core_api_url_env_precedence(monkeypatch):
    module = _reload_config(
        monkeypatch,
        DELPI_AUTH_CORE_API_URL="http://core-a:8000",
        CORE_API_URL="http://core-b:8000",
    )
    settings = module.Settings()
    assert settings.CORE_API_URL == "http://core-a:8000"
