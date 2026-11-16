"""ATLAS journal activation is intentionally split from normal Portal TI deploy."""
from pathlib import Path
from unittest.mock import Mock

import pytest

from it_portal_app.config import settings
from it_portal_app.infrastructure.persistence import db, migrations_runner

MIGRATION = "V016__atlas_deploy_oci_journal.sql"


def test_v016_exists_but_default_migration_gate_denies(monkeypatch):
    migration = next(
        path for version, path in migrations_runner._migration_files()
        if path.name == MIGRATION and version == 16
    )
    monkeypatch.setattr(settings, "ATLAS_JOURNAL_SCHEMA_APPLY_ENABLED", False)
    assert migrations_runner._migration_explicitly_enabled(migration) is False
    # The existing inventory migrations do not require the extra ATLAS gate.
    assert migrations_runner._migration_explicitly_enabled(
        Path("V015__workstation_bootstrap_signed_proof.sql")
    ) is True
    monkeypatch.setattr(settings, "ATLAS_JOURNAL_SCHEMA_APPLY_ENABLED", True)
    assert migrations_runner._migration_explicitly_enabled(migration) is True


def test_versioned_sql_is_safe_on_application_deploy():
    path = migrations_runner.MIGRATIONS_DIR / MIGRATION
    sql = path.read_text(encoding="utf-8")
    assert "EXPLICITLY GATED" in sql
    for table in ("challenges", "proposals", "events", "oci_bindings"):
        assert f"CREATE TABLE it_portal.atlas_deploy_{table}" in sql
    assert "CREATE TRIGGER atlas_oci_binding_immutable" in sql
    assert "CREATE TRIGGER atlas_oci_proposal_identity_guard" in sql
    assert "REVOKE ALL ON FUNCTION it_portal.atlas_oci_guard_binding()" in sql
    assert "REVOKE ALL ON TABLE" in sql
    # Migration must never grant CREATE, DML privileges or Core access by itself.
    assert not any(s in sql.upper() for s in (
        "CREATE ROLE ", "GRANT ALL ", "GRANT SELECT ", "DROP TABLE ",
        "ALTER ROLE ", "GRANT EXECUTE "
    ))


def _configured(monkeypatch):
    monkeypatch.setattr(settings, "DB_HOST", "localhost")
    monkeypatch.setattr(settings, "DB_PORT", "5432")
    monkeypatch.setattr(settings, "DB_NAME", "example_test_only")
    monkeypatch.setattr(settings, "DB_USER", "app_writer")
    monkeypatch.setattr(settings, "DB_PASSWORD", "test-writer-password")
    monkeypatch.setattr(settings, "DB_SSLMODE", "prefer")
    monkeypatch.setattr(settings, "ATLAS_JOURNAL_READ_DB_USER", "")
    monkeypatch.setattr(settings, "ATLAS_JOURNAL_READ_DB_PASSWORD", "")


def test_journal_reader_requires_distinct_explicit_role(monkeypatch):
    _configured(monkeypatch)
    assert db.atlas_journal_read_db_configured() is False
    with pytest.raises(RuntimeError, match="atlas_journal_reader_not_configured"):
        db.atlas_journal_read_connect()

    monkeypatch.setattr(settings, "ATLAS_JOURNAL_READ_DB_USER", "app_writer")
    monkeypatch.setattr(settings, "ATLAS_JOURNAL_READ_DB_PASSWORD", "same-role")
    assert db.atlas_journal_read_db_configured() is False

    monkeypatch.setattr(settings, "ATLAS_JOURNAL_READ_DB_USER", "atlas_readonly")
    assert db.atlas_journal_read_db_configured() is True


def test_journal_reader_enforces_connection_level_read_only(monkeypatch):
    _configured(monkeypatch)
    monkeypatch.setattr(settings, "ATLAS_JOURNAL_READ_DB_USER", "atlas_readonly")
    monkeypatch.setattr(settings, "ATLAS_JOURNAL_READ_DB_PASSWORD", "test-only-password")
    spy = Mock()
    monkeypatch.setattr(db.psycopg, "connect", spy)
    db.atlas_journal_read_connect()
    assert spy.call_count == 1
    kwargs = spy.call_args.kwargs
    assert kwargs["user"] == "atlas_readonly"
    assert kwargs["password"] == "test-only-password"
    assert kwargs["user"] != settings.DB_USER
    assert "default_transaction_read_only=on" in kwargs["options"]
    assert kwargs["application_name"] == "it-portal-atlas-journal-read"


def test_composable_env_gates_never_default_to_true():
    root = Path(__file__).resolve().parents[2]
    compose = (root / "infra/docker-compose.yml").read_text(encoding="utf-8")
    sample = (root / "infra/.env.prod.example").read_text(encoding="utf-8")
    for name in (
        "IT_PORTAL_ATLAS_JOURNAL_READ_ENABLED",
        "IT_PORTAL_ATLAS_JOURNAL_SCHEMA_APPLY_ENABLED",
    ):
        assert "$" + "{" + name + ":-false}" in compose
        assert f"{name}=false" in sample
    assert "IT_PORTAL_ATLAS_JOURNAL_READ_DB_PASSWORD:" in compose
