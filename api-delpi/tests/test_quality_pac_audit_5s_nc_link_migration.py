from __future__ import annotations

from pathlib import Path


def test_v013_audit_5s_nc_link_migration_declares_foreign_key():
    migration = (
        Path(__file__).resolve().parents[1]
        / "migrations"
        / "plugins"
        / "quality-action-plans"
        / "V013__pac_audit_5s_nc_link.sql"
    )

    sql = migration.read_text(encoding="utf-8")

    assert "linked_audit_5s_nc_id UUID" in sql
    assert "REFERENCES quality.audit_5s_nonconformities (id)" in sql
    assert "ON DELETE SET NULL" in sql
