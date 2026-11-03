"""PROC-0076 R12 — persistent metal quotes, real-PostgreSQL evidence.

Runs the *permitted* persistent path end-to-end against a provably
disposable PostgreSQL (same guard as ``test_market_data_repository_pg``):
catalog retention flipped to ``permanent`` + ``store`` inside the
disposable database — the exact catalog change the future approval
migration will perform — then proves insert, reference-date fidelity,
provenance, idempotent re-runs, history preservation, source scoping,
feed freshness and run-level concurrency. No production row is created
or modified; MetalCharts stays ``ttl_cache`` until the rights gate.
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

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
        host=host, port=port, dbname=dbname, user=user,
        password=password, sslmode="disable", connect_timeout=5,
        row_factory=dict_row,
    ) as probe:
        validate_target(host=host, dbname=dbname, conn=probe)

    original = {
        k: getattr(Settings, k) for k in (
            "PLUGINS_DB_HOST", "PLUGINS_DB_PORT", "PLUGINS_DB_NAME",
            "PLUGINS_DB_USER", "PLUGINS_DB_PASSWORD", "PLUGINS_DB_SSLMODE",
        )
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
def migrated(pg_env):
    """Fresh schema per file — same drop+re-apply convention as
    ``test_market_r2_pg`` so several PG files coexist in one session."""
    from app.infrastructure.persistence import migrations_runner
    from app.infrastructure.persistence.plugins_db import get_connection

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("DROP SCHEMA IF EXISTS external_data CASCADE")
        conn.commit()
    applied = migrations_runner.run_migrations()
    assert applied
    yield applied
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("DROP SCHEMA IF EXISTS external_data CASCADE")
        conn.commit()


@pytest.fixture()
def repo(migrated):
    from app.infrastructure.persistence.plugins_db import get_connection
    from app.infrastructure.persistence.market_data_repository import (
        MarketDataRepository,
    )

    with get_connection() as conn:
        yield MarketDataRepository(conn, schema="external_data")


def _grant_permanent(repo):
    """Simulate the future approved-rights catalog update — only ever
    inside the disposable database."""
    with repo._conn.cursor() as cur:
        cur.execute(
            "UPDATE external_data.market_data_sources "
            "SET observation_retention = 'permanent', "
            "    allowed_use_scope = 'collect;store;derive;"
            "internal_display;no_redistribute' "
            "WHERE source_id = 'metalcharts'"
        )
    repo.commit()


def _clear_quote_tables(repo):
    """Deterministic isolation — each test owns its observation set."""
    with repo._conn.cursor() as cur:
        cur.execute("DELETE FROM external_data.metal_quote_cache")
        cur.execute("DELETE FROM external_data.metal_quote_observations")
    repo.commit()


def _observations(repo, source_id="metalcharts"):
    with repo._conn.cursor() as cur:
        cur.execute(
            "SELECT o.observation_date, o.native_price, o.quote_basis, "
            "       o.source_record_key, o.observation_timestamp, "
            "       o.retrieved_at, i.instrument_code, o.unit_code "
            "FROM external_data.metal_quote_observations o "
            "JOIN external_data.metal_instruments i "
            "  ON i.instrument_id = o.instrument_id "
            "WHERE o.source_id = %s "
            "ORDER BY i.instrument_code, o.observation_date",
            (source_id,),
        )
        return cur.fetchall()


def _cache_count(repo):
    with repo._conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM external_data.metal_quote_cache")
        return cur.fetchone()["n"]


class _SpotProvider:
    def __init__(self, payload, configured=True):
        self.payload = payload
        self._configured = configured
        self.calls = 0

    def configured(self):
        return self._configured

    def fetch_spot(self):
        self.calls += 1
        return self.payload

    def fetch_history(self, symbol, date_from, date_to):
        return []


class _HistoryProvider:
    def __init__(self, bars):
        self.bars = bars

    def configured(self):
        return True

    def fetch_spot(self):
        return {}

    def fetch_history(self, symbol, date_from, date_to):
        return self.bars


def _spot_payload(ts="2026-11-03T17:30:00Z", price="6.70"):
    return {
        symbol: {
            "price": Decimal(price),
            "bid": Decimal("6.69"),
            "ask": Decimal("6.71"),
            "timestamp": ts,
            "exchange": exchange,
            "market_type": market_type,
            "stale": False,
            "currency": "USD",
            "unit": "usd_per_pound",
        }
        for symbol, exchange, market_type in (
            ("HG", "COMEX", "futures"),
            ("ALI", "LME", "spot"),
            ("NI", "LME", "spot"),
            ("ZN", "SPOT", "spot"),
            ("PB", "SPOT", "spot"),
        )
    }


def _enable(monkeypatch, feed_flag):
    from app.infrastructure.config.settings import Settings

    monkeypatch.setattr(Settings, feed_flag, True)


def test_permanent_prices_run_persists_and_is_idempotent(repo, monkeypatch):
    """AC-02/03/04 — one real shaped collection inserts 5 observations
    keyed by provider date; a second run changes nothing; a new day
    adds a row and preserves the old ones."""
    from app.application.market_data_ingestion import (
        MarketDataIngestionService,
    )

    _enable(monkeypatch, "EXTERNAL_DATA_FEED_METALS_PRICES_DAILY_ENABLED")
    _grant_permanent(repo)
    _clear_quote_tables(repo)
    now = datetime(2026, 11, 3, 20, 45, tzinfo=timezone.utc)
    provider = _SpotProvider(_spot_payload())
    service = MarketDataIngestionService(
        repository=repo, metalcharts_provider=provider, clock=lambda: now
    )

    first = service.run(
        "metals-prices-daily",
        date_from=date(2026, 11, 3),
        date_to=date(2026, 11, 3),
    )
    repo.commit()
    assert first.outcome == "success"
    assert first.inserted_count == 5
    assert provider.calls == 1

    rows = _observations(repo)
    assert len(rows) == 5
    assert {r["instrument_code"] for r in rows} == {
        "aluminum", "copper", "lead", "nickel", "zinc"
    }
    copper = next(r for r in rows if r["instrument_code"] == "copper")
    assert copper["observation_date"] == date(2026, 11, 3)
    assert copper["native_price"] == Decimal("6.700000")
    assert copper["quote_basis"] == "comex_futures_last"
    assert copper["unit_code"] == "usd_per_pound"
    assert copper["source_record_key"] == "metalcharts:prices:HG:2026-11-03"
    assert copper["observation_timestamp"] == datetime(
        2026, 11, 3, 17, 30, tzinfo=timezone.utc
    )
    assert _cache_count(repo) == 0

    # Re-run: identical payload → zero duplicates.
    second = service.run(
        "metals-prices-daily",
        date_from=date(2026, 11, 3),
        date_to=date(2026, 11, 3),
    )
    repo.commit()
    assert second.outcome == "success"
    assert second.inserted_count == 0
    assert len(_observations(repo)) == 5

    # Next-day collection appends; previous rows untouched.
    provider.payload = _spot_payload(ts="2026-11-04T17:30:00Z")
    third = service.run(
        "metals-prices-daily",
        date_from=date(2026, 11, 4),
        date_to=date(2026, 11, 4),
    )
    repo.commit()
    assert third.outcome == "success"
    assert third.inserted_count == 5
    rows = _observations(repo)
    assert len(rows) == 10
    assert {r["observation_date"] for r in rows} == {
        date(2026, 11, 3), date(2026, 11, 4)
    }


def test_permanent_read_scoped_to_effective_source(repo, monkeypatch):
    """AC-12/15 — the read path serves only the effective binding's
    source: Pink Sheet monthly rows never blend into the MetalCharts
    daily series."""
    from app.application import market_data_queries as mdq

    _grant_permanent(repo)
    _clear_quote_tables(repo)
    inst_now = datetime.now(timezone.utc)
    repo.upsert_metal_observation(
        instrument_id=repo.get_instrument("copper").instrument_id,
        observation_date=date(2026, 10, 1),
        native_price=Decimal("9500"),
        native_currency="USD",
        unit_code="metric_ton",
        quote_basis="monthly_average",
        source_id="world-bank-pink-sheet",
        source_record_key="pink-sheet:2026M10:Copper",
        retrieved_at=inst_now,
    )
    repo.upsert_metal_observation(
        instrument_id=repo.get_instrument("copper").instrument_id,
        observation_date=date(2026, 11, 3),
        native_price=Decimal("6.70"),
        native_currency="USD",
        unit_code="usd_per_pound",
        quote_basis="comex_futures_last",
        source_id="metalcharts",
        source_record_key="metalcharts:prices:HG:2026-11-03",
        retrieved_at=inst_now,
        observation_timestamp=datetime(
            2026, 11, 3, 17, 30, tzinfo=timezone.utc
        ),
    )
    repo.commit()

    payload = mdq.list_metal_observations(
        instrument_code="copper",
        date_from_raw="2026-01-01",
        date_to_raw="2026-12-31",
        limit_raw=None,
        cursor_raw=None,
    )
    assert payload["meta"]["source_ids"] == ["metalcharts"]
    assert len(payload["items"]) == 1
    item = payload["items"][0]
    assert item["observation_date"] == "2026-11-03"
    assert item["quote_basis"] == "comex_futures_last"
    assert item["source"]["source_id"] == "metalcharts"

    # Repo level: the other source's rows are still queryable by owner.
    rows = repo.list_metal_observations(
        instrument_id=repo.get_instrument("copper").instrument_id,
        source_id="world-bank-pink-sheet",
        date_from=date(2026, 1, 1),
        date_to=date(2026, 12, 31),
        limit=10,
    )
    assert [r["observation_date"] for r in rows] == [date(2026, 10, 1)]


def test_permanent_history_feed_persists_closes(repo, monkeypatch):
    """R12 — metals-daily under permanent retention writes daily
    closes to the observation table, not the TTL cache."""
    from app.application.market_data_ingestion import (
        MarketDataIngestionService,
    )

    _enable(monkeypatch, "EXTERNAL_DATA_FEED_METALS_DAILY_ENABLED")
    _grant_permanent(repo)
    _clear_quote_tables(repo)
    bars = [
        {
            "observation_date": date(2026, 11, 2),
            "open": Decimal("6.5"), "high": Decimal("6.7"),
            "low": Decimal("6.4"), "close": Decimal("6.69"),
            "volume": 100,
        },
        {
            "observation_date": date(2026, 11, 3),
            "open": Decimal("6.6"), "high": Decimal("6.8"),
            "low": Decimal("6.5"), "close": Decimal("6.72"),
            "volume": 120,
        },
    ]
    service = MarketDataIngestionService(
        repository=repo, metalcharts_provider=_HistoryProvider(bars)
    )
    result = service.run(
        "metals-daily",
        date_from=date(2026, 11, 1),
        date_to=date(2026, 11, 3),
    )
    repo.commit()
    assert result.outcome == "success"
    assert result.inserted_count == 10  # 5 bound instruments × 2 bars
    rows = _observations(repo)
    assert len(rows) == 10
    copper = next(r for r in rows if r["instrument_code"] == "copper")
    assert copper["quote_basis"] == "comex_daily_close"
    assert copper["observation_timestamp"] is None
    assert {r["quote_basis"] for r in rows} == {
        "comex_daily_close", "lme_daily_close", "spot_daily_close"
    }
    assert _cache_count(repo) == 0


def test_feed_status_reflects_permanent_observations(repo, monkeypatch):
    """R12 — feed freshness counts the permanent table when the source
    policy is 'permanent' (AC-14 honest 'last reference date')."""
    from app.application.market_data_ingestion import (
        MarketDataIngestionService,
    )

    _enable(monkeypatch, "EXTERNAL_DATA_FEED_METALS_PRICES_DAILY_ENABLED")
    _grant_permanent(repo)
    _clear_quote_tables(repo)
    service = MarketDataIngestionService(
        repository=repo,
        metalcharts_provider=_SpotProvider(_spot_payload()),
    )
    service.run(
        "metals-prices-daily",
        date_from=date(2026, 11, 3),
        date_to=date(2026, 11, 3),
    )
    repo.commit()

    statuses = {f["feed"]: f for f in repo.feed_statuses()}
    feed = statuses["metals-prices-daily"]
    assert feed["latest_observation_date"] == date(2026, 11, 3)
    assert feed["observation_count"] == 5
    assert feed["last_outcome"] == "success"


def test_failed_run_preserves_existing_history(repo, monkeypatch):
    """AC-04/14 — a provider failure after a successful collection
    never deletes or invalidates the authorized history."""
    from app.application.contracts import ProviderUnavailableError
    from app.application.market_data_ingestion import (
        MarketDataIngestionService,
    )

    _enable(monkeypatch, "EXTERNAL_DATA_FEED_METALS_PRICES_DAILY_ENABLED")
    _grant_permanent(repo)
    _clear_quote_tables(repo)
    service = MarketDataIngestionService(
        repository=repo,
        metalcharts_provider=_SpotProvider(_spot_payload()),
    )
    service.run(
        "metals-prices-daily",
        date_from=date(2026, 11, 3),
        date_to=date(2026, 11, 3),
    )
    repo.commit()
    assert len(_observations(repo)) == 5

    class _Down:
        def configured(self):
            return True

        def fetch_spot(self):
            raise ProviderUnavailableError("egress blocked")

        def fetch_history(self, *a):
            return []

    failing = MarketDataIngestionService(
        repository=repo, metalcharts_provider=_Down()
    )
    result = failing.run(
        "metals-prices-daily",
        date_from=date(2026, 11, 4),
        date_to=date(2026, 11, 4),
    )
    repo.commit()
    assert result.outcome == "failed"
    assert len(_observations(repo)) == 5  # history intact


def test_concurrent_runs_serialize_and_no_duplicates(repo, monkeypatch):
    """AC-03 — the advisory lock rejects a second concurrent run;
    concurrent upserts of the same identity converge to one row."""
    from concurrent.futures import ThreadPoolExecutor

    from app.application.market_data_ingestion import (
        IngestionLockedError,
        MarketDataIngestionService,
    )
    from app.infrastructure.persistence.plugins_db import get_connection
    from app.infrastructure.persistence.market_data_repository import (
        MarketDataRepository,
    )

    _enable(monkeypatch, "EXTERNAL_DATA_FEED_METALS_PRICES_DAILY_ENABLED")
    _grant_permanent(repo)
    _clear_quote_tables(repo)
    # Lock held by THIS session — a run on another connection is rejected.
    assert repo.try_advisory_lock(76007606) is True
    try:
        with get_connection() as other_conn:
            other_repo = MarketDataRepository(
                other_conn, schema="external_data"
            )
            other = MarketDataIngestionService(
                repository=other_repo,
                metalcharts_provider=_SpotProvider(_spot_payload()),
            )
            with pytest.raises(IngestionLockedError):
                other.run(
                    "metals-prices-daily",
                    date_from=date(2026, 11, 3),
                    date_to=date(2026, 11, 3),
                )
    finally:
        repo.release_advisory_lock(76007606)

    inst = repo.get_instrument("copper")
    now = datetime.now(timezone.utc)

    def _upsert(i):
        with get_connection() as conn:
            r = MarketDataRepository(conn, schema="external_data")
            out = r.upsert_metal_observation(
                instrument_id=inst.instrument_id,
                observation_date=date(2026, 11, 3),
                native_price=Decimal("6.70"),
                native_currency="USD",
                unit_code="usd_per_pound",
                quote_basis="comex_futures_last",
                source_id="metalcharts",
                source_record_key="metalcharts:prices:HG:2026-11-03",
                retrieved_at=now,
            )
            conn.commit()
            return out

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(_upsert, range(4)))
    assert sorted(results) == ["inserted", "unchanged", "unchanged", "unchanged"]
    rows = repo.list_metal_observations(
        instrument_id=inst.instrument_id,
        source_id="metalcharts",
        date_from=date(2026, 11, 3),
        date_to=date(2026, 11, 3),
        limit=10,
    )
    assert len(rows) == 1
