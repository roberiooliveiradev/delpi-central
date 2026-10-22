from pathlib import Path

from app.infrastructure.persistence.migrations_runner import (
    MIGRATIONS_DIR,
    SCHEMA_NAME,
    list_migration_files,
    parse_version_and_name,
)


def test_migrations_dir_and_v001_exist():
    assert MIGRATIONS_DIR.exists()
    files = list_migration_files()
    versions = [parse_version_and_name(path)[0] for path in files]
    assert "V001" in versions
    assert SCHEMA_NAME == "supplies"


def test_v001_sql_defines_preferences_uuid_pk():
    sql = (Path(MIGRATIONS_DIR) / "V001__create_supplies_schema.sql").read_text(
        encoding="utf-8"
    )
    assert "supply_user_preferences" in sql
    assert "user_id UUID PRIMARY KEY" in sql
    assert "keycloak_sub TEXT" in sql


def test_v002_defines_enrichment_tables_and_constraints():
    sql = (Path(MIGRATIONS_DIR) / "V002__supplier_enrichment_reviews.sql").read_text(
        encoding="utf-8"
    )
    # Four tables: review + proposals + decisions + append-only events.
    for table in (
        "supplier_enrichment_reviews",
        "supplier_enrichment_proposals",
        "supplier_enrichment_decisions",
        "supplier_enrichment_events",
    ):
        assert f"CREATE TABLE supplies.{table}" in sql
    # Server-side UUID keys, FK integrity, optimistic concurrency,
    # idempotency and audit fields.
    assert "DEFAULT gen_random_uuid()" in sql
    assert sql.count("REFERENCES supplies.supplier_enrichment_reviews") >= 3
    assert "ON DELETE RESTRICT" in sql
    assert "revision INTEGER NOT NULL" in sql
    assert "UNIQUE (review_id, idempotency_key)" in sql
    assert "UNIQUE (review_id, field_key)" in sql
    assert "expires_at TIMESTAMPTZ NOT NULL" in sql
    # Actor ownership scope is a hard column, not a runtime flag.
    assert "actor_subject UUID NOT NULL" in sql
    # No tax_id / raw external payload columns anywhere in the schema.
    assert "\n    tax_id" not in sql
    assert "raw_payload" not in sql
    # Additive only — never drop/truncate existing structures.
    for forbidden in ("DROP TABLE", "TRUNCATE", "DELETE FROM"):
        assert forbidden not in sql
