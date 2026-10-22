"""Migration V010 — relatórios metalográficos no schema engineering."""

from __future__ import annotations

from pathlib import Path

MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "plugins"
    / "engineering"
    / "V010__metallographic_reports.sql"
)


def test_v010_exists_and_does_not_rewrite_previous_files() -> None:
    folder = MIGRATION.parent
    assert MIGRATION.exists()
    assert (folder / "V009__lmp_nonconformity_occurrence_date.sql").exists()
    assert "DROP TABLE" not in MIGRATION.read_text(encoding="utf-8").upper()


def test_v010_defines_identity_concurrency_and_images() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "engineering.metallographic_reports" in sql
    assert "engineering.metallographic_report_images" in sql
    assert "engineering.metallographic_report_idempotency" in sql
    assert "engineering.metallographic_report_audit" in sql
    assert "engineering.metallographic_report_counters" in sql
    assert "UNIQUE (report_number)" in sql
    assert "UNIQUE (actor_subject, operation, idempotency_key)" in sql
    assert "deleted_at" in sql
    assert "version" in sql
    assert "'original'" in sql and "'measured'" in sql
    assert "'conforming'" in sql and "'nonconforming'" in sql
    assert "REFERENCES engineering.metallographic_reports" in sql


def test_v011_daily_numbers_keep_history_and_refuse_overflow() -> None:
    path = MIGRATION.parent / "V011__metallographic_report_daily_numbers.sql"
    sql = path.read_text(encoding="utf-8")
    assert "engineering.metallographic_business_date" in sql
    assert "engineering.metallographic_report_day_counters" in sql
    assert "engineering.metallographic_report_number_renames" in sql
    assert "America/Sao_Paulo" in sql
    assert "ORDER BY created_at, id" in sql
    assert "deleted_at IS NULL" not in sql
    assert "last_value <= 999" in sql
    assert "renumber aborted" in sql
    assert "DROP TABLE" not in sql.upper()
    assert "DROP SCHEMA" not in sql.upper()
