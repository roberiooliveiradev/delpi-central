"""PROC-0076 R11 — metals-prices-daily feed: /v1/prices last-quote
refresh, rights gates, budget, retention routing and basis semantics."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from app.application.contracts import (
    ProviderUnavailableError,
    RateLimitedError,
)
from app.application.market_data_ingestion import (
    FeedDisabledError,
    MarketDataIngestionService,
)
from app.domain.market_data import (
    FEED_METALS_PRICES_DAILY,
    PROVIDER_METALCHARTS,
    RETENTION_PERMANENT,
    RETENTION_TTL_CACHE,
    MarketDataSource,
    MetalInstrumentBinding,
    spot_last_quote_basis,
)
from app.infrastructure.config.settings import Settings


def _mc_source(active=True, scope=None, retention=RETENTION_TTL_CACHE):
    return MarketDataSource(
        source_id=PROVIDER_METALCHARTS,
        provider_id=PROVIDER_METALCHARTS,
        source_kind="api",
        attribution="MetalCharts",
        license_reference="https://metalcharts.org/api-terms",
        license_reviewed_at=None,
        allowed_use_scope=scope
        or "collect;derive;internal_display;store_cache_only;"
        "no_redistribute",
        active=active,
        observation_retention=retention,
    )


def _binding(active=True, key="HG", instrument_id=7):
    return MetalInstrumentBinding(
        binding_id=1,
        instrument_id=instrument_id,
        instrument_code="copper",
        source_id=PROVIDER_METALCHARTS,
        source_series_key=key,
        granularity="day",
        quotation_basis="comex_daily_close",
        native_currency="USD",
        unit_code="usd_per_pound",
        priority=10,
        active=active,
    )


class _Repo:
    def __init__(self, **kw):
        self.kw = kw
        self.cache_upserts = []
        self.obs_upserts = []
        self.finished = None
        self.purged = 0
        self.recorded_calls = []

    def try_advisory_lock(self, key):
        return self.kw.get("lock_ok", True)

    def release_advisory_lock(self, key):
        pass

    def commit(self):
        pass

    def rollback(self):
        pass

    def get_source(self, source_id):
        return self.kw.get("sources", {}).get(source_id)

    def list_instrument_sources(self, **kw):
        out = self.kw.get("bindings", [])
        if kw.get("source_id") is not None:
            out = [b for b in out if b.source_id == kw["source_id"]]
        if kw.get("active_only"):
            out = [b for b in out if b.active]
        return out

    def create_ingestion_run(self, **kw):
        return "run-1"

    def finish_ingestion_run(self, run_id, **kw):
        self.finished = kw

    def upsert_metal_cache(self, **kw):
        self.cache_upserts.append(kw)
        return self.kw.get("cache_outcome", "inserted")

    def upsert_metal_observation(self, **kw):
        self.obs_upserts.append(kw)
        return self.kw.get("obs_outcome", "inserted")

    def purge_expired_cache(self):
        self.purged += 1
        return 0

    def sum_api_call_weight(self, *, source_id, since):
        return 0

    def record_api_call(self, **kw):
        self.recorded_calls.append(kw)
        return True


class _SpotProvider:
    def __init__(self, payload=None, exc=None, configured=True):
        self.payload = payload or {}
        self.exc = exc
        self._configured = configured
        self.calls = 0

    def configured(self):
        return self._configured

    def fetch_spot(self):
        self.calls += 1
        if self.exc:
            raise self.exc
        return self.payload


def _enable(monkeypatch):
    monkeypatch.setattr(
        Settings, "EXTERNAL_DATA_FEED_METALS_PRICES_DAILY_ENABLED", True
    )


def _spot_payload(price="6.70", stale=False, **over):
    entry = {
        "price": Decimal(price) if price is not None else None,
        "bid": Decimal("6.69"),
        "ask": Decimal("6.71"),
        "timestamp": "2026-10-30T17:30:00Z",
        "exchange": "COMEX",
        "market_type": "futures",
        "stale": stale,
        "currency": "USD",
        "unit": "usd_per_pound",
    }
    entry.update(over)
    return {"HG": entry}


# --- gates -------------------------------------------------------------------


def test_disabled_feed_refuses(monkeypatch):
    service = MarketDataIngestionService(repository=_Repo())
    with pytest.raises(FeedDisabledError):
        service.run(
            FEED_METALS_PRICES_DAILY,
            date_from=date(2026, 10, 30),
            date_to=date(2026, 10, 30),
        )


def test_ttl_source_without_cache_scope_fails(monkeypatch):
    """A collect+store scope does NOT satisfy the TTL-cache gate — the
    ops are distinct on purpose."""
    _enable(monkeypatch)
    src = _mc_source(scope="collect;store;derive;internal_display")
    repo = _Repo(sources={PROVIDER_METALCHARTS: src})
    service = MarketDataIngestionService(
        repository=repo, metalcharts_provider=_SpotProvider()
    )
    result = service.run(
        FEED_METALS_PRICES_DAILY,
        date_from=date(2026, 10, 30),
        date_to=date(2026, 10, 30),
    )
    assert result.outcome == "failed"
    assert result.error_code == "EXTERNAL_DATA_SOURCE_NOT_LICENSED"


def test_permanent_source_without_store_fails(monkeypatch):
    """retention='permanent' + missing 'store' → fail-closed, never
    written to the permanent table."""
    _enable(monkeypatch)
    src = _mc_source(
        scope="collect;derive;internal_display;store_cache_only",
        retention=RETENTION_PERMANENT,
    )
    repo = _Repo(sources={PROVIDER_METALCHARTS: src})
    service = MarketDataIngestionService(
        repository=repo, metalcharts_provider=_SpotProvider()
    )
    result = service.run(
        FEED_METALS_PRICES_DAILY,
        date_from=date(2026, 10, 30),
        date_to=date(2026, 10, 30),
    )
    assert result.outcome == "failed"
    assert result.error_code == "EXTERNAL_DATA_SOURCE_NOT_LICENSED"
    assert repo.obs_upserts == []


def test_no_key_fails(monkeypatch):
    _enable(monkeypatch)
    repo = _Repo(sources={PROVIDER_METALCHARTS: _mc_source()})
    service = MarketDataIngestionService(
        repository=repo,
        metalcharts_provider=_SpotProvider(configured=False),
    )
    result = service.run(
        FEED_METALS_PRICES_DAILY,
        date_from=date(2026, 10, 30),
        date_to=date(2026, 10, 30),
    )
    assert result.outcome == "failed"


def test_no_bindings_fails(monkeypatch):
    _enable(monkeypatch)
    repo = _Repo(
        sources={PROVIDER_METALCHARTS: _mc_source()},
        bindings=[_binding(active=False), _binding(key=None)],
    )
    service = MarketDataIngestionService(
        repository=repo, metalcharts_provider=_SpotProvider()
    )
    result = service.run(
        FEED_METALS_PRICES_DAILY,
        date_from=date(2026, 10, 30),
        date_to=date(2026, 10, 30),
    )
    assert result.outcome == "failed"
    assert result.error_code == "EXTERNAL_DATA_NO_APPROVED_SERIES"


# --- happy path ---------------------------------------------------------------


def test_spot_run_one_call_writes_ttl_cache(monkeypatch):
    _enable(monkeypatch)
    now = datetime(2026, 10, 30, 20, 45, tzinfo=timezone.utc)
    repo = _Repo(
        sources={PROVIDER_METALCHARTS: _mc_source()},
        bindings=[_binding()],
    )
    provider = _SpotProvider(payload=_spot_payload())
    service = MarketDataIngestionService(
        repository=repo,
        metalcharts_provider=provider,
        clock=lambda: now,
    )
    result = service.run(
        FEED_METALS_PRICES_DAILY,
        date_from=date(2026, 10, 30),
        date_to=date(2026, 10, 30),
    )
    assert result.outcome == "success"
    assert result.fetched_count == 1
    assert result.inserted_count == 1
    assert provider.calls == 1
    up = repo.cache_upserts[0]
    assert up["native_price"] == Decimal("6.70")
    assert up["observation_date"] == date(2026, 10, 30)
    assert up["observation_timestamp"] == datetime(
        2026, 10, 30, 17, 30, tzinfo=timezone.utc
    )
    assert up["quote_basis"] == "comex_futures_last"
    assert up["expires_at"] is not None
    assert repo.purged == 1
    # one ledger entry, weight 1, prices endpoint
    assert len(repo.recorded_calls) == 1
    assert repo.recorded_calls[0]["endpoint"] == "prices"
    assert repo.recorded_calls[0]["weight"] == 1


def test_epoch_timestamp_and_basis(monkeypatch):
    _enable(monkeypatch)
    repo = _Repo(
        sources={PROVIDER_METALCHARTS: _mc_source()},
        bindings=[_binding(key="ZN")],
    )
    payload = {
        "ZN": _spot_payload(
            timestamp=1793405400,  # 2026-10-31T00:10:00Z
            exchange="SPOT",
            market_type="spot",
        )["HG"]
    }
    service = MarketDataIngestionService(
        repository=repo,
        metalcharts_provider=_SpotProvider(payload=payload),
    )
    result = service.run(
        FEED_METALS_PRICES_DAILY,
        date_from=date(2026, 10, 31),
        date_to=date(2026, 10, 31),
    )
    assert result.outcome == "success"
    up = repo.cache_upserts[0]
    assert up["observation_date"] == date(2026, 10, 31)
    assert up["quote_basis"] == "spot_last"


def test_stale_and_missing_rows_skipped(monkeypatch):
    _enable(monkeypatch)
    repo = _Repo(
        sources={PROVIDER_METALCHARTS: _mc_source()},
        bindings=[
            _binding(key="HG", instrument_id=7),
            _binding(key="ALI", instrument_id=8),
            _binding(key="ZZ", instrument_id=9),
            _binding(key="NI", instrument_id=10),
        ],
    )
    payload = {
        "HG": _spot_payload()["HG"],
        "ALI": _spot_payload(stale=True)["HG"],
        # ZZ absent from payload entirely
        "NI": _spot_payload(timestamp=None)["HG"],
    }
    service = MarketDataIngestionService(
        repository=repo,
        metalcharts_provider=_SpotProvider(payload=payload),
    )
    result = service.run(
        FEED_METALS_PRICES_DAILY,
        date_from=date(2026, 10, 30),
        date_to=date(2026, 10, 30),
    )
    assert result.outcome == "success"
    assert result.fetched_count == 4
    assert result.inserted_count == 1
    assert result.skipped_count == 3
    assert len(repo.cache_upserts) == 1


# --- failure taxonomy ---------------------------------------------------------


def test_rate_limited_marks_failed_no_uncontrolled_retry(monkeypatch):
    _enable(monkeypatch)
    repo = _Repo(sources={PROVIDER_METALCHARTS: _mc_source()},
                 bindings=[_binding()])
    provider = _SpotProvider(
        exc=RateLimitedError("429", retry_after=60)
    )
    service = MarketDataIngestionService(
        repository=repo, metalcharts_provider=provider
    )
    result = service.run(
        FEED_METALS_PRICES_DAILY,
        date_from=date(2026, 10, 30),
        date_to=date(2026, 10, 30),
    )
    assert result.outcome == "failed"
    assert provider.calls == 1  # no hot retry inside the run
    assert repo.cache_upserts == []


def test_provider_unavailable_marks_failed(monkeypatch):
    _enable(monkeypatch)
    repo = _Repo(sources={PROVIDER_METALCHARTS: _mc_source()},
                 bindings=[_binding()])
    provider = _SpotProvider(exc=ProviderUnavailableError("egress blocked"))
    service = MarketDataIngestionService(
        repository=repo, metalcharts_provider=provider
    )
    result = service.run(
        FEED_METALS_PRICES_DAILY,
        date_from=date(2026, 10, 30),
        date_to=date(2026, 10, 30),
    )
    assert result.outcome == "failed"
    assert result.error_code == "EXTERNAL_DATA_PROVIDER_UNAVAILABLE"


# --- permanent routing (rights-gated, ready-not-enabled) ---------------------


def test_permanent_retention_writes_observations(monkeypatch):
    """A source whose rights are later proven (retention=permanent +
    collect+store) routes rows to the permanent table — the write path
    is ready even while MetalCharts stays ttl_cache."""
    _enable(monkeypatch)
    src = _mc_source(
        scope="collect;store;derive;internal_display",
        retention=RETENTION_PERMANENT,
    )
    repo = _Repo(
        sources={PROVIDER_METALCHARTS: src},
        bindings=[_binding()],
    )
    service = MarketDataIngestionService(
        repository=repo,
        metalcharts_provider=_SpotProvider(payload=_spot_payload()),
    )
    result = service.run(
        FEED_METALS_PRICES_DAILY,
        date_from=date(2026, 10, 30),
        date_to=date(2026, 10, 30),
    )
    assert result.outcome == "success"
    assert len(repo.obs_upserts) == 1
    assert repo.cache_upserts == []
    assert repo.obs_upserts[0]["quote_basis"] == "comex_futures_last"
    assert repo.purged == 0


# --- basis mapping ------------------------------------------------------------


@pytest.mark.parametrize(
    "exchange,market_type,expected",
    [
        ("COMEX", "futures", "comex_futures_last"),
        ("LME", "spot", "lme_spot_last"),
        ("SPOT", "spot", "spot_last"),
        (None, None, "unknown_spot_last"),
        ("comex", None, "comex_spot_last"),
    ],
)
def test_spot_last_quote_basis(exchange, market_type, expected):
    assert spot_last_quote_basis(exchange, market_type) == expected
