"""Startup migrations gate — degraded boot must never take CNPJ down
(PROC-0076 R1).

The service's primary contract (X0/X1 CNPJ) is stateless; a missing
schema grant or a failed migration leaves market-data routes answering
503 while the rest of the app still comes up.
"""

from __future__ import annotations

import pytest

from app.create_app import create_app
from app.infrastructure.config.settings import Settings
from app.startup.run_migrations_on_startup import run_migrations_on_startup


def test_boot_skipped_when_db_not_configured(monkeypatch):
    monkeypatch.setattr(Settings, "PLUGINS_DB_HOST", "")
    monkeypatch.setattr(Settings, "PLUGINS_DB_NAME", "")
    monkeypatch.setattr(Settings, "PLUGINS_DB_USER", "")
    monkeypatch.setattr(Settings, "PLUGINS_DB_PASSWORD", "")
    called = []
    monkeypatch.setattr(
        "app.infrastructure.persistence.migrations_runner.run_migrations",
        lambda: called.append(True),
    )
    monkeypatch.setattr(Settings, "RUN_MIGRATIONS_ON_STARTUP", True)
    run_migrations_on_startup()
    assert called == []


def test_boot_survives_migration_failure(monkeypatch):
    """Migration error → logged degraded boot, app still created with
    the CNPJ surface registered (AC-R1-16/17)."""
    monkeypatch.setattr(Settings, "RUN_MIGRATIONS_ON_STARTUP", True)
    monkeypatch.setattr(Settings, "PLUGINS_DB_HOST", "db")
    monkeypatch.setattr(Settings, "PLUGINS_DB_NAME", "plugins")
    monkeypatch.setattr(Settings, "PLUGINS_DB_USER", "u")
    monkeypatch.setattr(Settings, "PLUGINS_DB_PASSWORD", "p")

    def _boom():
        raise RuntimeError("schema grant denied")

    monkeypatch.setattr(
        "app.infrastructure.persistence.migrations_runner.run_migrations",
        _boom,
    )
    run_migrations_on_startup()  # must not raise

    app = create_app()
    rules = {r.rule for r in app.url_map.iter_rules()}
    assert any("/v1/cnpj/" in rule for rule in rules)


def test_boot_applies_pending_migrations(monkeypatch):
    monkeypatch.setattr(Settings, "RUN_MIGRATIONS_ON_STARTUP", True)
    monkeypatch.setattr(Settings, "PLUGINS_DB_HOST", "db")
    monkeypatch.setattr(Settings, "PLUGINS_DB_NAME", "plugins")
    monkeypatch.setattr(Settings, "PLUGINS_DB_USER", "u")
    monkeypatch.setattr(Settings, "PLUGINS_DB_PASSWORD", "p")
    called = []
    monkeypatch.setattr(
        "app.infrastructure.persistence.migrations_runner.run_migrations",
        lambda: called.append(True) or ["V001"],
    )
    run_migrations_on_startup()
    assert called == [True]


def test_boot_skipped_when_flag_disabled(monkeypatch):
    monkeypatch.setattr(Settings, "RUN_MIGRATIONS_ON_STARTUP", False)
    monkeypatch.setattr(Settings, "PLUGINS_DB_HOST", "db")
    monkeypatch.setattr(Settings, "PLUGINS_DB_NAME", "plugins")
    monkeypatch.setattr(Settings, "PLUGINS_DB_USER", "u")
    monkeypatch.setattr(Settings, "PLUGINS_DB_PASSWORD", "p")
    called = []
    monkeypatch.setattr(
        "app.infrastructure.persistence.migrations_runner.run_migrations",
        lambda: called.append(True),
    )
    run_migrations_on_startup()
    assert called == []
