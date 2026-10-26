"""Real-PostgreSQL proof of contract readiness (PROC-0076 R1.3).

Scenario A/B/C/D against an actual engine: a database at V001–V003
(legacy catalog carrying the literal ``internal_display`` grant) must
be denied, V004-applied must be ready, and checksum divergence must
deny — all before any market-data read. Requires the same provably
disposable PostgreSQL as ``test_market_data_repository_pg.py``.
"""

from __future__ import annotations

import os

import pytest

from app.application.contracts import ContractNotReadyError
from app.infrastructure.persistence import migrations_runner
from app.infrastructure.persistence.market_contract_readiness import (
    REQUIRED_CONTRACT_REVISION,
    check_market_contract_ready,
)

pytestmark = pytest.mark.skipif(
    not os.getenv("EXTERNAL_DATA_TEST_PG_HOST"),
    reason="EXTERNAL_DATA_TEST_PG_HOST not set — isolated PostgreSQL required",
)


@pytest.fixture(scope="session")
def pg_env():
    """Same fail-closed wiring as the repository PG suite."""
    import psycopg
    from psycopg.rows import dict_row

    from app.infrastructure.config.settings import Settings
    from tests.pg_disposable_guard import validate_target

    host = os.environ["EXTERNAL_DATA_TEST_PG_HOST"]
    port = int(os.getenv("EXTERNAL_DATA_TEST_PG_PORT", "5432"))
    dbname = os.getenv("EXTERNAL_DATA_TEST_PG_NAME", "external_data_test")
    user = os.getenv("EXTERNAL_DATA_TEST_PG_USER", "postgres")
    password = os.getenv("EXTERNAL_DATA_TEST_PG_PASSWORD", "test")

    with psycopg.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
        sslmode="disable",
        connect_timeout=5,
        row_factory=dict_row,
    ) as probe:
        validate_target(host=host, dbname=dbname, conn=probe)

    original = {
        "PLUGINS_DB_HOST": Settings.PLUGINS_DB_HOST,
        "PLUGINS_DB_PORT": Settings.PLUGINS_DB_PORT,
        "PLUGINS_DB_NAME": Settings.PLUGINS_DB_NAME,
        "PLUGINS_DB_USER": Settings.PLUGINS_DB_USER,
        "PLUGINS_DB_PASSWORD": Settings.PLUGINS_DB_PASSWORD,
        "PLUGINS_DB_SSLMODE": Settings.PLUGINS_DB_SSLMODE,
    }
    Settings.PLUGINS_DB_HOST = host
    Settings.PLUGINS_DB_PORT = port
    Settings.PLUGINS_DB_NAME = dbname
    Settings.PLUGINS_DB_USER = user
    Settings.PLUGINS_DB_PASSWORD = password
    Settings.PLUGINS_DB_SSLMODE = "disable"
    yield
    for key, value in original.items():
        setattr(Settings, key, value)


@pytest.fixture(autouse=True)
def _guard_before_mutation(pg_env):
    from app.infrastructure.persistence.plugins_db import get_connection
    from tests.pg_disposable_guard import verify_disposable

    with get_connection() as conn:
        verify_disposable(conn)
    yield


@pytest.fixture(scope="session")
def migrated_v1_v3(pg_env):
    """Apply ONLY V001–V003 — simulates the legacy catalog state that
    still carries the literal ``internal_display`` grant."""
    from app.infrastructure.persistence.plugins_db import get_connection

    files = [
        m
        for m in migrations_runner.list_migration_files()
        if m.version < REQUIRED_CONTRACT_REVISION
    ]
    with get_connection() as conn:
        migrations_runner.ensure_migrations_table(conn)
        for migration in files:
            migrations_runner.apply_migration(conn, migration)
    yield
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DROP SCHEMA external_data CASCADE")
        conn.commit()


def test_v003_catalog_is_denied(migrated_v1_v3):
    """Scenario A/B: V004 absent — legacy catalog must not serve."""
    from app.infrastructure.persistence.plugins_db import get_connection

    with get_connection() as conn:
        with pytest.raises(ContractNotReadyError):
            check_market_contract_ready(conn)


def test_use_cases_deny_under_v003(migrated_v1_v3):
    """The whole read surface fails closed under the legacy schema —
    no LME price can leave the API."""
    from app.application import market_data_queries as mdq

    with pytest.raises(ContractNotReadyError):
        mdq.get_catalog()
    with pytest.raises(ContractNotReadyError):
        mdq.list_metal_observations(
            instrument_code="copper",
            date_from_raw="2020-01-01",
            date_to_raw="2026-12-31",
            limit_raw=None,
            cursor_raw=None,
        )
    with pytest.raises(ContractNotReadyError):
        mdq.list_fx_observations(
            pair="USD/BRL",
            rate_kind="ptax_closing_sell",
            date_from_raw="2026-01-01",
            date_to_raw="2026-12-31",
            limit_raw=None,
            cursor_raw=None,
        )
    with pytest.raises(ContractNotReadyError):
        mdq.get_ingestion_status()


def test_v004_applied_is_ready_and_scope_enforced(migrated_v1_v3):
    """Scenario C: V004 applied → readiness OK, pending LME display
    still denied by the use-policy layer, FX allowed."""
    from app.application import market_data_queries as mdq
    from app.application.contracts import UseNotApprovedError
    from app.infrastructure.persistence.plugins_db import get_connection

    v004 = next(
        m
        for m in migrations_runner.list_migration_files()
        if m.version == REQUIRED_CONTRACT_REVISION
    )
    with get_connection() as conn:
        migrations_runner.apply_migration(conn, v004)
        check_market_contract_ready(conn)  # must not raise

    catalog = mdq.get_catalog()
    pink_sheet = [
        i for i in catalog["instruments"] if i["kind"] == "metal"
    ]
    assert pink_sheet
    assert all(i["display_allowed"] is False for i in pink_sheet)
    assert catalog["fx_series"][0]["display_allowed"] is True

    with pytest.raises(UseNotApprovedError):
        mdq.list_metal_observations(
            instrument_code="copper",
            date_from_raw="2020-01-01",
            date_to_raw="2026-12-31",
            limit_raw=None,
            cursor_raw=None,
        )
    # FX stays available under its approved grant.
    fx = mdq.list_fx_observations(
        pair="USD/BRL",
        rate_kind="ptax_closing_sell",
        date_from_raw="2026-01-01",
        date_to_raw="2026-12-31",
        limit_raw=None,
        cursor_raw=None,
    )
    assert fx["items"] == []  # no data, but served — not denied


def test_tampered_v004_checksum_denies(migrated_v1_v3):
    """Scenario D: ledger checksum divergence fails closed."""
    from app.infrastructure.persistence.plugins_db import get_connection

    v004 = next(
        m
        for m in migrations_runner.list_migration_files()
        if m.version == REQUIRED_CONTRACT_REVISION
    )
    with get_connection() as conn:
        migrations_runner.apply_migration(conn, v004)
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE external_data.schema_migrations "
                "SET checksum = 'tampered' WHERE version = %s",
                (REQUIRED_CONTRACT_REVISION,),
            )
        conn.commit()
        with pytest.raises(ContractNotReadyError):
            check_market_contract_ready(conn)
