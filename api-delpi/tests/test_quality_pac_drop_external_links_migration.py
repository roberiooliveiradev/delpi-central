from __future__ import annotations

from pathlib import Path


def test_v016_drop_pac_external_entity_links_migration():
    migration = (
        Path(__file__).resolve().parents[1]
        / "migrations"
        / "plugins"
        / "quality-action-plans"
        / "V016__drop_pac_external_entity_links.sql"
    )

    sql = migration.read_text(encoding="utf-8")

    assert "DROP COLUMN IF EXISTS linked_kaizen_id" in sql
    assert "DROP COLUMN IF EXISTS linked_audit_5s_nc_id" in sql
    assert "fk_quality_action_plans_linked_kaizen" in sql
    assert "fk_quality_action_plans_linked_audit_5s_nc" in sql
