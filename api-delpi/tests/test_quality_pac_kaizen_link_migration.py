from __future__ import annotations

from pathlib import Path


def test_v012_kaizen_link_migration_declares_foreign_key():
    migration = (
        Path(__file__).resolve().parents[1]
        / "migrations"
        / "plugins"
        / "quality-action-plans"
        / "V012__pac_kaizen_link.sql"
    )

    sql = migration.read_text(encoding="utf-8")

    assert "linked_kaizen_id UUID" in sql
    assert "REFERENCES quality.kaizens (id)" in sql
    assert "ON DELETE SET NULL" in sql
