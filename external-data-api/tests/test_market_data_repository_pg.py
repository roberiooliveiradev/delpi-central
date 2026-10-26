"""Real PostgreSQL integration — migrations, constraints, upserts.

Requires an isolated PostgreSQL reachable through EXTERNAL_DATA_TEST_PG_*
env vars. When unset, every case is skipped (TEST_NOT_RUN — environment),
matching the repo convention for real-engine proofs. These tests prove
migration-from-empty, upgrade path, uniqueness, decimal integrity and
idempotent re-ingestion against the actual engine.
"""

from __future__ import annotations

import os
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from app.infrastructure.persistence import migrations_runner
from app.infrastructure.persistence.market_data_repository import (
    MarketDataRepository,
)

pytestmark = pytest.mark.skipif(
    not os.getenv("EXTERNAL_DATA_TEST_PG_HOST"),
    reason="EXTERNAL_DATA_TEST_PG_HOST not set — isolated PostgreSQL required",
)


@pytest.fixture(scope="session")
def pg_env():
    """Point Settings at an isolated *database* (never another schema —
    ``external_data`` is canonical and immutable)."""
    from app.infrastructure.config.settings import Settings

    original = {
        "PLUGINS_DB_HOST": Settings.PLUGINS_DB_HOST,
        "PLUGINS_DB_PORT": Settings.PLUGINS_DB_PORT,
        "PLUGINS_DB_NAME": Settings.PLUGINS_DB_NAME,
        "PLUGINS_DB_USER": Settings.PLUGINS_DB_USER,
        "PLUGINS_DB_PASSWORD": Settings.PLUGINS_DB_PASSWORD,
        "PLUGINS_DB_SSLMODE": Settings.PLUGINS_DB_SSLMODE,
    }
    Settings.PLUGINS_DB_HOST = os.environ["EXTERNAL_DATA_TEST_PG_HOST"]
    Settings.PLUGINS_DB_PORT = int(
        os.getenv("EXTERNAL_DATA_TEST_PG_PORT", "5432")
    )
    Settings.PLUGINS_DB_NAME = os.getenv(
        "EXTERNAL_DATA_TEST_PG_NAME", "external_data_test"
    )
    Settings.PLUGINS_DB_USER = os.getenv(
        "EXTERNAL_DATA_TEST_PG_USER", "postgres"
    )
    Settings.PLUGINS_DB_PASSWORD = os.getenv(
        "EXTERNAL_DATA_TEST_PG_PASSWORD", "test"
    )
    Settings.PLUGINS_DB_SSLMODE = "disable"
    yield
    for key, value in original.items():
        setattr(Settings, key, value)


@pytest.fixture(scope="session")
def migrated(pg_env):
    """Empty → apply all migrations (migration-empty proof)."""
    applied = migrations_runner.run_migrations()
    assert applied  # at least V001 + V002 on an empty schema
    # Re-running is a no-op (upgrade/idempotent path).
    assert migrations_runner.run_migrations() == []
    yield
    # Disposable database: leave it as found.
    from app.infrastructure.persistence.plugins_db import get_connection

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("DROP SCHEMA IF EXISTS external_data CASCADE")
        conn.commit()


@pytest.fixture()
def repo(migrated):
    from app.infrastructure.persistence.plugins_db import get_connection

    with get_connection() as conn:
        yield MarketDataRepository(
            conn, schema=migrations_runner._schema()
        )


def test_catalog_seed_present(repo):
    sources = {s.source_id: s for s in repo.list_sources()}
    assert sources["bcb-ptax"].active is True
    assert "ODbL" in sources["bcb-ptax"].license_reference
    instruments = {i.instrument_code: i for i in repo.list_instruments()}
    assert instruments["copper"].granularity == "month"
    assert instruments["copper"].native_currency == "USD"


def test_metal_observation_upsert_idempotent(repo):
    inst = repo.get_instrument("copper")
    now = datetime.now(timezone.utc)
    first = repo.upsert_metal_observation(
        instrument_id=inst.instrument_id,
        observation_date=date(2026, 9, 1),
        native_price=Decimal("9500.5"),
        native_currency="USD",
        unit_code="metric_ton",
        quote_basis="monthly_average",
        source_id="world-bank-pink-sheet",
        source_record_key="pink-sheet:2026M09:Copper",
        retrieved_at=now,
    )
    repo.commit()
    assert first == "inserted"

    second = repo.upsert_metal_observation(
        instrument_id=inst.instrument_id,
        observation_date=date(2026, 9, 1),
        native_price=Decimal("9500.5"),
        native_currency="USD",
        unit_code="metric_ton",
        quote_basis="monthly_average",
        source_id="world-bank-pink-sheet",
        source_record_key="pink-sheet:2026M09:Copper",
        retrieved_at=now,
    )
    repo.commit()
    assert second == "unchanged"

    revised = repo.upsert_metal_observation(
        instrument_id=inst.instrument_id,
        observation_date=date(2026, 9, 1),
        native_price=Decimal("9501.0"),
        native_currency="USD",
        unit_code="metric_ton",
        quote_basis="monthly_average",
        source_id="world-bank-pink-sheet",
        source_record_key="pink-sheet:2026M09:Copper",
        retrieved_at=now,
    )
    repo.commit()
    assert revised == "updated"

    rows = repo.list_metal_observations(
        instrument_id=inst.instrument_id,
        date_from=date(2026, 9, 1),
        date_to=date(2026, 9, 30),
        limit=10,
    )
    assert len(rows) == 1
    assert rows[0]["native_price"] == Decimal("9501.000000")
    assert rows[0]["revised_at"] is not None


def test_fx_upsert_and_read(repo):
    now = datetime.now(timezone.utc)
    out = repo.upsert_fx_observation(
        pair_code="USD/BRL",
        rate_kind="ptax_closing_sell",
        reference_date=date(2026, 10, 9),
        value=Decimal("5.4321"),
        source_id="bcb-ptax",
        source_record_key="ptax:2026-10-09",
        retrieved_at=now,
    )
    repo.commit()
    assert out == "inserted"
    rows = repo.list_fx_observations(
        pair_code="USD/BRL",
        rate_kind="ptax_closing_sell",
        date_from=date(2026, 10, 1),
        date_to=date(2026, 10, 31),
        limit=10,
    )
    assert len(rows) == 1
    assert rows[0]["value"] == Decimal("5.432100")


def test_non_positive_value_rejected_by_check(repo):
    import psycopg

    inst = repo.get_instrument("copper")
    with pytest.raises(psycopg.errors.CheckViolation):
        repo.upsert_metal_observation(
            instrument_id=inst.instrument_id,
            observation_date=date(2026, 8, 1),
            native_price=Decimal("0"),
            native_currency="USD",
            unit_code="metric_ton",
            quote_basis="monthly_average",
            source_id="world-bank-pink-sheet",
            source_record_key="x",
            retrieved_at=datetime.now(timezone.utc),
        )
    repo.rollback()


def test_ingestion_run_bookkeeping(repo):
    run_id = repo.create_ingestion_run(
        provider_id="bcb-ptax",
        feed="fx-daily",
        correlation_id="corr-1",
        version="proc-0076-p0-v1",
    )
    repo.finish_ingestion_run(
        run_id,
        outcome="success",
        fetched_count=2,
        inserted_count=2,
        updated_count=0,
        skipped_count=0,
        safe_error_code=None,
    )
    repo.commit()
    statuses = {f["feed"]: f for f in repo.feed_statuses()}
    assert statuses["fx-daily"]["last_outcome"] == "success"


def test_checksum_divergence_fails(migrated, tmp_path):
    """Mutating an applied migration file must break validation."""
    files = migrations_runner.list_migration_files()
    target = files[0].path
    original = target.read_bytes()
    try:
        target.write_bytes(original + b"\n-- mutation\n")
        from app.infrastructure.persistence.plugins_db import (
            get_connection,
        )

        with get_connection() as conn, pytest.raises(
            migrations_runner.MigrationError
        ):
            migrations_runner.validate_migration_history(conn, files)
    finally:
        target.write_bytes(original)


def test_fk_violation_rejected(repo):
    """Observation referencing a nonexistent instrument fails on the FK."""
    import psycopg

    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        repo.upsert_metal_observation(
            instrument_id=999999,
            observation_date=date(2026, 9, 1),
            native_price=Decimal("1"),
            native_currency="USD",
            unit_code="metric_ton",
            quote_basis="monthly_average",
            source_id="world-bank-pink-sheet",
            source_record_key="fk-test",
            retrieved_at=datetime.now(timezone.utc),
        )
    repo.rollback()


def test_unlicensed_source_fk_blocks_insert(repo):
    """A source absent from the catalog cannot receive observations —
    the FK is the last line of licensing enforcement."""
    import psycopg

    inst = repo.get_instrument("copper")
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        repo.upsert_metal_observation(
            instrument_id=inst.instrument_id,
            observation_date=date(2026, 9, 1),
            native_price=Decimal("1"),
            native_currency="USD",
            unit_code="metric_ton",
            quote_basis="monthly_average",
            source_id="lme-unlicensed",
            source_record_key="fk-test",
            retrieved_at=datetime.now(timezone.utc),
        )
    repo.rollback()


def test_decimal_precision_roundtrip(repo):
    """NUMERIC(20,6) preserves six fractional digits exactly."""
    inst = repo.get_instrument("nickel")
    now = datetime.now(timezone.utc)
    repo.upsert_metal_observation(
        instrument_id=inst.instrument_id,
        observation_date=date(2026, 9, 1),
        native_price=Decimal("18123.456789"),
        native_currency="USD",
        unit_code="metric_ton",
        quote_basis="monthly_average",
        source_id="world-bank-pink-sheet",
        source_record_key="precision-test",
        retrieved_at=now,
    )
    repo.commit()
    rows = repo.list_metal_observations(
        instrument_id=inst.instrument_id,
        date_from=date(2026, 9, 1),
        date_to=date(2026, 9, 30),
        limit=10,
    )
    assert rows[0]["native_price"] == Decimal("18123.456789")


def test_concurrent_workers_serialize_migrations(migrated):
    """Multi-worker boot: N concurrent ``run_migrations`` calls must
    serialize on the advisory lock — no catalog race, exactly one
    recorded version per migration."""
    from concurrent.futures import ThreadPoolExecutor

    from app.infrastructure.persistence.plugins_db import get_connection

    # Reset to empty inside the disposable database, then race workers.
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("DROP SCHEMA external_data CASCADE")
        conn.commit()

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: migrations_runner.run_migrations(), range(4)))

    applied_flat = {v for versions in results for v in versions}
    assert applied_flat  # at least one worker applied V001/V002

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT version FROM external_data.schema_migrations ORDER BY 1"
        )
        versions = [r["version"] for r in cur.fetchall()]
        cur.execute(
            "SELECT count(*) AS n FROM information_schema.tables "
            "WHERE table_schema='external_data'"
        )
        tables = cur.fetchone()["n"]
    # One row per migration file — concurrent workers converged.
    assert len(versions) == len(set(versions))
    assert {"V001", "V002"} <= set(versions)
    assert tables >= 6


def test_second_startup_reports_no_pending(migrated):
    """Restart proof: once applied, a fresh run reports nothing pending."""
    assert migrations_runner.run_migrations() == []
