import importlib
import logging

import pytest

import engineering_app.config as config_module


@pytest.fixture(autouse=True)
def _restore_config():
    yield
    importlib.reload(config_module)


def _reload_config(monkeypatch, **env):
    for key in (
        "SERVICE_NAME",
        "ENGINEERING_API_ROOT_PATH",
        "PORT",
        "APP_ENV",
        "LOG_LEVEL",
    ):
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
    forbidden_fragments = ("secret", "password", "token", "key")
    for attr in public_attrs:
        assert not any(fragment in attr.lower() for fragment in forbidden_fragments)
