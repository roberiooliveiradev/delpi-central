from __future__ import annotations

from pathlib import Path


def test_v014_ishikawa_causes_jsonb_migration_converts_six_m_columns():
    migration = (
        Path(__file__).resolve().parents[1]
        / "migrations"
        / "plugins"
        / "quality-action-plans"
        / "V014__ishikawa_causes_jsonb.sql"
    )

    sql = migration.read_text(encoding="utf-8")

    for column in (
        "machine",
        "method_process",
        "material",
        "manpower",
        "measurement",
        "environment",
    ):
        assert f"ALTER COLUMN {column} TYPE JSONB" in sql

    assert "SET DEFAULT '[]'::jsonb" in sql
