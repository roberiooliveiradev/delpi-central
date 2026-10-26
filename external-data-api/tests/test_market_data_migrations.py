"""Static migration contract tests (PROC-0076).

The schema must be dedicated, idempotent-safe, additive and free of
destructive statements — the same assertions other plugin APIs enforce.
"""

from pathlib import Path

from app.infrastructure.persistence.migrations_runner import (
    MIGRATIONS_DIR,
    list_migration_files,
)


def _files():
    return {m.version: m for m in list_migration_files()}


def test_migrations_dir_and_versions_exist():
    files = _files()
    assert MIGRATIONS_DIR.exists()
    assert {"V001", "V002"} <= set(files)


def _sql(version: str) -> str:
    """Migration body without comment lines."""
    text = Path(_files()[version].path).read_text(encoding="utf-8")
    return "\n".join(
        line for line in text.splitlines() if not line.strip().startswith("--")
    )


def test_v001_creates_dedicated_schema_and_tables():
    sql = _sql("V001")
    assert "CREATE SCHEMA IF NOT EXISTS external_data" in sql
    for table in (
        "market_data_sources",
        "metal_instruments",
        "metal_quote_observations",
        "fx_rate_observations",
        "market_data_ingestion_runs",
    ):
        assert f"CREATE TABLE external_data.{table}" in sql
    # Money is never float.
    assert "NUMERIC" in sql
    assert "FLOAT" not in sql.upper()
    # Idempotency by economic identity + source.
    assert "UNIQUE (instrument_id, observation_date, source_id)" in sql
    assert (
        "UNIQUE (pair_code, rate_kind, reference_date, source_id)" in sql
    )
    # Positive value invariant — no fabricated zeros.
    assert "CHECK (native_price > 0)" in sql
    assert "CHECK (value > 0)" in sql
    # No destructive statements.
    for forbidden in ("DROP TABLE", "TRUNCATE", "DELETE FROM"):
        assert forbidden not in sql


def test_v001_does_not_touch_other_schemas():
    sql = Path(_files()["V001"].path).read_text(encoding="utf-8")
    assert "supplies." not in sql
    assert "public." not in sql


def test_v002_seeds_licensed_sources_and_instruments():
    sql = Path(_files()["V002"].path).read_text(encoding="utf-8")
    assert "'bcb-ptax'" in sql
    assert "'world-bank-pink-sheet'" in sql
    # License references recorded, not implied.
    assert "ODbL" in sql
    assert "CC BY 4.0" in sql
    assert "license_reviewed_at" in sql
    for instrument in (
        "copper",
        "aluminum",
        "zinc",
        "nickel",
        "lead",
        "tin",
    ):
        assert f"'{instrument}'" in sql
    # Unlicensed sources are never seeded (checked on literals, comments
    # may document why they are absent).
    assert "'lme'" not in sql.lower()
    assert "'shockmetais'" not in sql.lower()
    for forbidden in ("DROP TABLE", "TRUNCATE", "DELETE FROM"):
        assert forbidden not in sql
