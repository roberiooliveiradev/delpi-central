import os

from app.startup.run_plugins_migrations_on_startup import (
    _is_enabled,
    run_plugins_migrations_on_startup,
)


def test_is_enabled_accepts_common_truthy_values(monkeypatch):
    for value in ("true", "TRUE", "1", "yes", "on"):
        monkeypatch.setenv("RUN_PLUGINS_MIGRATIONS_ON_STARTUP", value)
        assert _is_enabled() is True


def test_is_enabled_defaults_to_false(monkeypatch):
    monkeypatch.delenv("RUN_PLUGINS_MIGRATIONS_ON_STARTUP", raising=False)
    assert _is_enabled() is False


def test_startup_skips_when_disabled(monkeypatch):
    monkeypatch.setenv("RUN_PLUGINS_MIGRATIONS_ON_STARTUP", "false")
    run_plugins_migrations_on_startup()
