"""Real-PostgreSQL proof of the R2 schema (PROC-0076 R2).

V005 applied to a provably disposable engine: catalog seeds, FK/unique
constraints, idempotent upserts and the new read use cases — including
the negative path for an unapproved NCM. The LME quarantine and the
existing tables must be unaffected.
"""

from __future__ import annotations

import os
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from app.infrastructure.persistence import migrations_runner

pytestmark = pytest.mark.skipif(
    not os.getenv("EXTERNAL_DATA_TEST_PG_HOST"),
    reason="EXTERNAL_DATA_TEST_PG_HOST not set — isolated PostgreSQL required",
)


@pytest.fixture(scope="session")
def pg_env():
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


@pytest.fixture()
def migrated(pg_env):
    """Full migration run on a clean schema; teardown drops it so
    sibling suites always start empty."""
    from app.infrastructure.persistence.plugins_db import get_connection

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DROP SCHEMA IF EXISTS external_data CASCADE")
        conn.commit()
    applied = migrations_runner.run_migrations()
    assert applied
    yield applied
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DROP SCHEMA external_data CASCADE")
        conn.commit()


def _allowlist(conn, ncm="12345678", description="Test NCM"):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO external_data.comex_ncm_allowlist "
            "(ncm_code, ncm_version, description, family_code, "
            " approved_by, approved_at) "
            "VALUES (%s, 'NCM2022', %s, 'metals', 'test', NOW())",
            (ncm, description),
        )
    conn.commit()


def test_v005_applies_and_seeds(migrated):
    from app.infrastructure.persistence.plugins_db import get_connection

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT source_id, active, allowed_use_scope "
                "FROM external_data.market_data_sources "
                "WHERE source_id IN ('mdic-comex-stat','ibge-ipp-sidra') "
                "ORDER BY source_id"
            )
            rows = {r["source_id"]: r for r in cur.fetchall()}
    assert set(rows) == {"mdic-comex-stat", "ibge-ipp-sidra"}
    # Feeds are OFF until operational authorization.
    assert rows["mdic-comex-stat"]["active"] is False
    assert rows["ibge-ipp-sidra"]["active"] is False
    assert "internal_display" in rows["ibge-ipp-sidra"]["allowed_use_scope"]


def test_ipp_series_seeded_canonical(migrated):
    from app.infrastructure.persistence.plugins_db import get_connection
    from app.infrastructure.persistence.market_data_repository import (
        MarketDataRepository,
    )

    with get_connection() as conn:
        repo = MarketDataRepository(conn, schema="external_data")
        series = {s["series_id"]: s for s in repo.list_producer_price_series()}
    assert "ipp-metalurgia-index" in series
    assert "ipp-metalurgia-mom" in series
    idx = series["ipp-metalurgia-index"]
    assert idx["table_code"] == "6903"
    assert idx["activity_code"] == "46641"
    assert idx["variable_code"] == "10008"
    assert idx["base_reference"] == "dez/2018=100"


def test_comex_upsert_idempotent_and_fk(migrated):
    from app.infrastructure.persistence.plugins_db import get_connection
    from app.infrastructure.persistence.market_data_repository import (
        MarketDataRepository,
    )

    kw = dict(
        reference_month=date(2026, 8, 1),
        ncm_code="12345678",
        ncm_version="NCM2022",
        country_code="160",
        state_code="SC",
        fob_usd_total=Decimal("14000"),
        net_weight_kg_total=Decimal("4000"),
        unit_value_usd_per_t=Decimal("3500"),
        contributing_rows=2,
        quality_status="validated",
        dataset_year=2026,
        dataset_revision=None,
        source_checksum="abc",
        source_id="mdic-comex-stat",
        retrieved_at=datetime(2026, 9, 5, tzinfo=timezone.utc),
    )
    with get_connection() as conn:
        # FK: unapproved NCM cannot be persisted.
        with pytest.raises(Exception):
            MarketDataRepository(conn, schema="external_data"
                                 ).upsert_comex_observation(**kw)
        conn.rollback()
        _allowlist(conn)
        repo = MarketDataRepository(conn, schema="external_data")
        assert repo.upsert_comex_observation(**kw) == "inserted"
        conn.commit()
        # Idempotent re-import: same values → unchanged; revision → updated.
        assert repo.upsert_comex_observation(**kw) == "unchanged"
        kw2 = dict(kw, fob_usd_total=Decimal("15000"),
                   unit_value_usd_per_t=Decimal("3750"))
        assert repo.upsert_comex_observation(**kw2) == "updated"
        conn.commit()


def test_ipp_upsert_idempotent(migrated):
    from app.infrastructure.persistence.plugins_db import get_connection
    from app.infrastructure.persistence.market_data_repository import (
        MarketDataRepository,
    )

    kw = dict(
        series_id="ipp-metalurgia-index",
        reference_month=date(2026, 8, 1),
        value=Decimal("184.02"),
        source_id="ibge-ipp-sidra",
        source_record_key="sidra:10008:46641:202608",
        published_at=None,
        retrieved_at=datetime(2026, 9, 5, tzinfo=timezone.utc),
    )
    with get_connection() as conn:
        repo = MarketDataRepository(conn, schema="external_data")
        assert repo.upsert_producer_price_observation(**kw) == "inserted"
        conn.commit()
        assert repo.upsert_producer_price_observation(**kw) == "unchanged"
        kw2 = dict(kw, value=Decimal("184.03"))
        assert repo.upsert_producer_price_observation(**kw2) == "updated"
        conn.commit()


def test_read_paths_round_trip(migrated):
    """Persisted rows are served by the use cases; unapproved NCM → 404."""
    from app.application import market_data_queries as mdq
    from app.application.contracts import UnknownSeriesError
    from app.infrastructure.persistence.plugins_db import get_connection
    from app.infrastructure.persistence.market_data_repository import (
        MarketDataRepository,
    )

    with get_connection() as conn:
        _allowlist(conn)
        repo = MarketDataRepository(conn, schema="external_data")
        repo.upsert_comex_observation(
            reference_month=date(2026, 8, 1),
            ncm_code="12345678",
            ncm_version="NCM2022",
            country_code="160",
            state_code="SC",
            fob_usd_total=Decimal("14000"),
            net_weight_kg_total=Decimal("4000"),
            unit_value_usd_per_t=Decimal("3500"),
            contributing_rows=2,
            quality_status="validated",
            dataset_year=2026,
            dataset_revision=None,
            source_checksum="abc",
            source_id="mdic-comex-stat",
            retrieved_at=datetime(2026, 9, 5, tzinfo=timezone.utc),
        )
        repo.upsert_producer_price_observation(
            series_id="ipp-metalurgia-index",
            reference_month=date(2026, 8, 1),
            value=Decimal("184.02"),
            source_id="ibge-ipp-sidra",
            source_record_key="k",
            published_at=None,
            retrieved_at=datetime(2026, 9, 5, tzinfo=timezone.utc),
        )
        conn.commit()

    catalog = mdq.get_catalog()
    comex = catalog["import_ncms"]
    assert comex and comex[0]["ncm_code"] == "12345678"
    assert comex[0]["display_allowed"] is True
    ipp = catalog["producer_price_series"]
    assert any(s["series_id"] == "ipp-metalurgia-index" for s in ipp)

    comex_payload = mdq.list_comex_imports(
        ncm_code="12345678",
        date_from_raw="2026-01-01",
        date_to_raw="2026-12-31",
        country_code=None,
        state_code=None,
        limit_raw=None,
        cursor_raw=None,
    )
    assert comex_payload["meta"]["data_status"] == "ok"
    assert comex_payload["items"][0]["unit_value_usd_per_t"] == (
        "3500.000000"
    )

    ipp_payload = mdq.list_producer_price_observations(
        series_id="ipp-metalurgia-index",
        date_from_raw="2026-01-01",
        date_to_raw="2026-12-31",
        limit_raw=None,
        cursor_raw=None,
    )
    assert ipp_payload["items"][0]["value"] == "184.020000"

    with pytest.raises(UnknownSeriesError):
        mdq.list_comex_imports(
            ncm_code="87654321",
            date_from_raw="2026-01-01",
            date_to_raw="2026-12-31",
            country_code=None,
            state_code=None,
            limit_raw=None,
            cursor_raw=None,
        )


def test_legacy_tables_unaffected(migrated):
    """V005 is additive — metal/FX history and quarantine catalog intact."""
    from app.application import market_data_queries as mdq
    from app.infrastructure.persistence.plugins_db import get_connection

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS n FROM external_data.metal_instruments"
            )
            metals = cur.fetchone()["n"]
    assert metals == 6
    catalog = mdq.get_catalog()
    pink = [i for i in catalog["instruments"] if i["kind"] == "metal"]
    assert all(i["display_allowed"] is False for i in pink)
