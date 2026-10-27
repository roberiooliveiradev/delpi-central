"""PROC-0076 R5 — MetalCharts adapter, budget, ingestion and read path.

Fixtures reproduce the contract verified on the public docs
(2026-10-27): ``{success, data: {SYMBOL: {...}}}`` spot envelope, HG =
COMEX copper quoted USD/lb, OHLCV history bars, weight 1/2 per call.
Live-call verification is TEST_NOT_RUN until a key is provisioned —
everything here runs against sanitized fixtures and fakes.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.application.contracts import (
    InvalidResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RateLimitedError,
    UseNotApprovedError,
)
from app.application.market_data_ingestion import (
    FeedDisabledError,
    MarketDataIngestionService,
)
from app.application.metalcharts_budget import MetalChartsBudget
from app.domain.market_data import (
    FEED_METALS_DAILY,
    PROVIDER_METALCHARTS,
    RETENTION_PERMANENT,
    RETENTION_TTL_CACHE,
    MetalInstrumentBinding,
    MarketDataSource,
)
from app.infrastructure.config.settings import Settings
from app.infrastructure.providers.metalcharts_provider import (
    MetalChartsProvider,
    params_hash,
)

import requests


# --- provider fixtures --------------------------------------------------------

def _resp(status=200, body=None, headers=None):
    class _R:
        def __init__(self):
            self.status_code = status
            self.headers = headers or {}
            self._body = body if body is not None else {}

        def json(self):
            if isinstance(self._body, Exception):
                raise self._body
            return self._body

    return _R()


SPOT_BODY = {
    "success": True,
    "data": {
        "HG": {
            "symbol": "HG",
            "price": 6.69766,
            "bid": 6.6943,
            "ask": 6.7010,
            "timestamp": "2026-09-26T18:12:50.484Z",
            "exchange": "COMEX",
            "marketType": "futures",
            "stale": False,
        },
        "SN": {
            "symbol": "SN",
            "price": None,
            "stale": True,
        },
    },
}

HISTORY_BODY_LIST = {
    "success": True,
    "data": [
        {"date": "2026-10-01", "open": 6.50, "high": 6.72,
         "low": 6.48, "close": 6.69, "volume": 12345},
        {"date": "2026-10-02", "open": 6.70, "high": 6.75,
         "low": 6.66, "close": 6.71, "volume": 12000},
        {"date": "2026-10-03", "close": None},  # incomplete → skipped
    ],
}

HISTORY_BODY_NESTED = {
    "success": True,
    "data": {"bars": [
        {"t": "2026-10-01T00:00:00Z", "o": 6.5, "h": 6.7,
         "l": 6.4, "c": 6.69, "v": 100},
    ]},
}


def _provider(body=None, status=200, headers=None):
    resp = _resp(status, body if body is not None else SPOT_BODY, headers)
    seen = []

    def transport(url, *, headers, timeout):
        seen.append(url)
        return resp

    provider = MetalChartsProvider(
        api_key="mc_live_test",
        base_url="https://api.metalcharts.org",
        transport=transport,
    )
    return provider, seen


class TestProviderContract:
    def test_spot_parses_verified_shape(self):
        provider, seen = _provider()
        out = provider.fetch_spot()
        assert "api.metalcharts.org/v1/prices" in seen[0]
        hg = out["HG"]
        assert hg["price"] == Decimal("6.69766")
        assert hg["exchange"] == "COMEX"
        assert hg["market_type"] == "futures"
        assert hg["stale"] is False
        # No silent zero — missing price stays None.
        assert out["SN"]["price"] is None

    def test_history_list_shape(self):
        provider, _ = _provider(body=HISTORY_BODY_LIST)
        bars = provider.fetch_history(
            "HG", date(2026, 9, 28), date(2026, 10, 3)
        )
        assert [b["observation_date"] for b in bars] == [
            date(2026, 10, 1),
            date(2026, 10, 2),
        ]
        assert bars[0]["close"] == Decimal("6.69")
        assert bars[0]["open"] == Decimal("6.5")

    def test_history_nested_shape(self):
        provider, _ = _provider(body=HISTORY_BODY_NESTED)
        bars = provider.fetch_history(
            "HG", date(2026, 9, 28), date(2026, 10, 3)
        )
        assert len(bars) == 1
        assert bars[0]["close"] == Decimal("6.69")

    def test_history_unparseable_rejected(self):
        provider, _ = _provider(
            body={"success": True, "data": {"unexpected": 1}}
        )
        with pytest.raises(InvalidResponseError):
            provider.fetch_history("HG", date(2026, 10, 1), date(2026, 10, 2))

    def test_envelope_not_success_rejected(self):
        provider, _ = _provider(
            body={"success": False, "error": "bad symbol"}
        )
        with pytest.raises(InvalidResponseError):
            provider.fetch_spot()

    def test_auth_denied_maps_unavailable(self):
        provider, _ = _provider(status=401)
        with pytest.raises(ProviderUnavailableError):
            provider.fetch_spot()

    def test_plan_forbidden_maps_unavailable(self):
        provider, _ = _provider(status=403)
        with pytest.raises(ProviderUnavailableError):
            provider.fetch_history("HG", date(2026, 10, 1), date(2026, 10, 2))

    def test_rate_limited_carries_retry_after(self):
        provider, _ = _provider(status=429, headers={"Retry-After": "37"})
        with pytest.raises(RateLimitedError) as exc:
            provider.fetch_spot()
        assert exc.value.retry_after == 37

    def test_server_error_maps_unavailable(self):
        provider, _ = _provider(status=503)
        with pytest.raises(ProviderUnavailableError):
            provider.fetch_spot()

    def test_timeout_maps_typed(self):
        def transport(url, *, headers, timeout):
            raise requests.Timeout()

        provider = MetalChartsProvider(
            api_key="k",
            base_url="https://api.metalcharts.org",
            transport=transport,
        )
        with pytest.raises(ProviderTimeoutError):
            provider.fetch_spot()

    def test_missing_key_refuses_before_request(self):
        called = []

        def transport(url, *, headers, timeout):
            called.append(url)

        provider = MetalChartsProvider(
            api_key="",
            base_url="https://api.metalcharts.org",
            transport=transport,
        )
        assert provider.configured() is False
        with pytest.raises(ProviderUnavailableError):
            provider.fetch_spot()
        assert called == []

    def test_host_allowlist_enforced(self):
        with pytest.raises(ProviderUnavailableError):
            MetalChartsProvider(
                api_key="k",
                base_url="https://evil.example.com",
            )

    def test_https_required(self):
        with pytest.raises(ProviderUnavailableError):
            MetalChartsProvider(
                api_key="k",
                base_url="http://api.metalcharts.org",
            )

    def test_invalid_interval_rejected(self):
        provider, _ = _provider()
        with pytest.raises(InvalidResponseError):
            provider.fetch_history(
                "HG", date(2026, 10, 1), date(2026, 10, 2),
                interval="1min",
            )

    def test_bearer_header_sent_not_logged(self):
        seen_headers = []

        def transport(url, *, headers, timeout):
            seen_headers.append(headers)
            return _resp(200, SPOT_BODY)

        provider = MetalChartsProvider(
            api_key="mc_live_secret",
            base_url="https://api.metalcharts.org",
            transport=transport,
        )
        provider.fetch_spot()
        assert seen_headers[0]["Authorization"] == "Bearer mc_live_secret"


# --- budget -------------------------------------------------------------------

class _LedgerRepo:
    def __init__(self, weights=None):
        self.weights = weights or {}
        self.recorded = []

    def sum_api_call_weight(self, *, source_id, since):
        for window, total in self.weights.items():
            if since <= window[0]:
                return total
        return 0

    def record_api_call(self, **kw):
        self.recorded.append(kw)
        return kw.get("dedup_hit", True)


def test_budget_monthly_exhausted():
    repo = _LedgerRepo()
    now = datetime(2026, 10, 27, 12, 0, tzinfo=timezone.utc)
    budget = MetalChartsBudget(
        repository=repo,
        monthly_budget=10,
        minute_budget=10,
        clock=lambda: now,
    )
    repo.weights = {(now.replace(day=1),): 9}
    with pytest.raises(RateLimitedError):
        budget.acquire(weight=2)


def test_budget_minute_exhausted_retry_after():
    repo = _LedgerRepo()
    now = datetime(2026, 10, 27, 12, 0, tzinfo=timezone.utc)
    budget = MetalChartsBudget(
        repository=repo,
        monthly_budget=100,
        minute_budget=2,
        clock=lambda: now,
    )
    repo.weights = {(now - timedelta(seconds=30),): 2}
    with pytest.raises(RateLimitedError) as exc:
        budget.acquire(weight=1)
    assert exc.value.retry_after == 60


def test_budget_allows_within_caps():
    repo = _LedgerRepo()
    budget = MetalChartsBudget(
        repository=repo, monthly_budget=200, minute_budget=10
    )
    budget.acquire(weight=2)  # no raise


# --- ingestion: metals-daily ---------------------------------------------------

def _mc_source(active=True, scope=None):
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
        observation_retention=RETENTION_TTL_CACHE,
    )


def _binding(active=True, key="HG"):
    return MetalInstrumentBinding(
        binding_id=1,
        instrument_id=7,
        instrument_code="copper",
        source_id=PROVIDER_METALCHARTS,
        source_series_key=key,
        granularity="day",
        quotation_basis="daily_close",
        native_currency="USD",
        unit_code="usd_per_pound",
        priority=10,
        active=active,
    )


class _McRepo:
    def __init__(self, **kw):
        self.kw = kw
        self.upserts = []
        self.purged = 0
        self.finished = None

    def try_advisory_lock(self, key):
        return True

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
        if kw.get("instrument_id") is not None:
            out = [
                b for b in out
                if b.instrument_id == kw["instrument_id"]
            ]
        return out

    def create_ingestion_run(self, **kw):
        return "run-1"

    def finish_ingestion_run(self, run_id, **kw):
        self.finished = kw

    def upsert_metal_cache(self, **kw):
        self.upserts.append(kw)
        return "inserted"

    def purge_expired_cache(self):
        self.purged += 1
        return 0

    def sum_api_call_weight(self, *, source_id, since):
        return 0

    def record_api_call(self, **kw):
        return True


class _McProvider:
    def __init__(self, bars=None, exc=None, configured=True):
        self.bars = bars or []
        self.exc = exc
        self.calls = []

    def configured(self):
        return self._configured if hasattr(self, "_configured") else True

    def fetch_history(self, symbol, date_from, date_to):
        self.calls.append((symbol, date_from, date_to))
        if self.exc:
            raise self.exc
        return self.bars


def _enable_daily(monkeypatch):
    monkeypatch.setattr(
        Settings, "EXTERNAL_DATA_FEED_METALS_DAILY_ENABLED", True
    )


def test_metals_daily_disabled_refuses(monkeypatch):
    service = MarketDataIngestionService(repository=_McRepo())
    with pytest.raises(FeedDisabledError):
        service.run(
            FEED_METALS_DAILY,
            date_from=date(2026, 10, 1),
            date_to=date(2026, 10, 27),
        )


def test_metals_daily_scope_gate(monkeypatch):
    """Permanent-store scope still fails the cache gate — the ops are
    distinct on purpose."""
    _enable_daily(monkeypatch)
    src = _mc_source(scope="collect;store;derive;internal_display")
    repo = _McRepo(sources={PROVIDER_METALCHARTS: src})
    service = MarketDataIngestionService(
        repository=repo, metalcharts_provider=_McProvider()
    )
    result = service.run(
        FEED_METALS_DAILY,
        date_from=date(2026, 10, 1),
        date_to=date(2026, 10, 27),
    )
    assert result.outcome == "failed"
    assert result.error_code == "EXTERNAL_DATA_SOURCE_NOT_LICENSED"


def test_metals_daily_no_key_fails(monkeypatch):
    _enable_daily(monkeypatch)
    repo = _McRepo(sources={PROVIDER_METALCHARTS: _mc_source()})
    provider = _McProvider()
    provider._configured = False
    service = MarketDataIngestionService(
        repository=repo, metalcharts_provider=provider
    )
    result = service.run(
        FEED_METALS_DAILY,
        date_from=date(2026, 10, 1),
        date_to=date(2026, 10, 27),
    )
    assert result.outcome == "failed"


def test_metals_daily_no_verified_bindings_fails(monkeypatch):
    _enable_daily(monkeypatch)
    repo = _McRepo(
        sources={PROVIDER_METALCHARTS: _mc_source()},
        bindings=[_binding(active=False), _binding(key=None)],
    )
    service = MarketDataIngestionService(
        repository=repo, metalcharts_provider=_McProvider()
    )
    result = service.run(
        FEED_METALS_DAILY,
        date_from=date(2026, 10, 1),
        date_to=date(2026, 10, 27),
    )
    assert result.outcome == "failed"
    assert result.error_code == "EXTERNAL_DATA_NO_APPROVED_SERIES"


def test_metals_daily_happy_path_writes_ttl_cache(monkeypatch):
    _enable_daily(monkeypatch)
    now = datetime(2026, 10, 27, 12, 0, tzinfo=timezone.utc)
    repo = _McRepo(
        sources={PROVIDER_METALCHARTS: _mc_source()},
        bindings=[_binding()],
    )
    provider = _McProvider(
        bars=[
            {
                "observation_date": date(2026, 10, 26),
                "open": Decimal("6.5"),
                "high": Decimal("6.7"),
                "low": Decimal("6.4"),
                "close": Decimal("6.69"),
                "volume": 100,
            }
        ]
    )
    service = MarketDataIngestionService(
        repository=repo,
        metalcharts_provider=provider,
        clock=lambda: now,
    )
    result = service.run(
        FEED_METALS_DAILY,
        date_from=date(2026, 10, 1),
        date_to=date(2026, 10, 27),
    )
    assert result.outcome == "success"
    assert result.fetched_count == 1
    assert result.inserted_count == 1
    assert provider.calls == [
        ("HG", date(2026, 10, 1), date(2026, 10, 27))
    ]
    up = repo.upserts[0]
    assert up["native_price"] == Decimal("6.69")
    assert up["unit_code"] == "usd_per_pound"
    assert up["source_id"] == PROVIDER_METALCHARTS
    assert up["expires_at"] == now + timedelta(
        hours=Settings.METALCHARTS_CACHE_TTL_HOURS
    )
    assert repo.purged == 1


# --- query path: effective binding ---------------------------------------------

from app.application import market_data_queries as mdq


class _QRepo:
    def __init__(self, **kw):
        self.kw = kw
        self.calls = []

    def list_sources(self):
        return self.kw["sources"]

    def get_source(self, source_id):
        return {s.source_id: s for s in self.kw["sources"]}.get(source_id)

    def list_instruments(self):
        return self.kw["instruments"]

    def get_instrument(self, code):
        return {
            i.instrument_code: i for i in self.kw["instruments"]
        }.get(code)

    def list_instrument_sources(self, **kw):
        self.calls.append(("bindings", kw))
        return self.kw.get("bindings", [])

    def latest_observation_dates(self):
        return {}

    def list_ncm_allowlist(self):
        return []

    def list_producer_price_series(self):
        return []

    def list_metal_observations(self, **kw):
        self.calls.append(("permanent", kw))
        return self.kw.get("permanent_rows", [])

    def list_metal_cache(self, **kw):
        self.calls.append(("cache", kw))
        return self.kw.get("cache_rows", [])


class _ConnCtx:
    def __enter__(self):
        return object()

    def __exit__(self, *exc):
        return False


def _wire_queries(monkeypatch, repo):
    monkeypatch.setattr(Settings, "plugins_db_configured",
                        classmethod(lambda cls: True))
    monkeypatch.setattr(mdq, "get_connection", lambda: _ConnCtx())
    monkeypatch.setattr(
        mdq, "MarketDataRepository", lambda conn, schema: repo
    )
    monkeypatch.setattr(
        mdq, "check_market_contract_ready", lambda conn: None
    )


def _q_instrument():
    return SimpleNamespace(
        instrument_id=7,
        instrument_code="copper",
        metal_code="copper",
        label="Cobre",
        market="world_bank_pink_sheet",
        quotation_basis="monthly_average",
        native_currency="USD",
        unit_code="metric_ton",
        unit_label="USD/metric ton",
        source_id="world-bank-pink-sheet",
        source_series_key="Copper",
        granularity="month",
        active=True,
    )


def _pink_source():
    return MarketDataSource(
        source_id="world-bank-pink-sheet",
        provider_id="world-bank-pink-sheet",
        source_kind="file",
        attribution="World Bank",
        license_reference="CC BY 4.0",
        license_reviewed_at=date(2026, 10, 26),
        allowed_use_scope=(
            "collect;store;derive;"
            "internal_display_pending_lme_review;"
            "no_redistribution_pending_lme_review"
        ),
        active=True,
        observation_retention=RETENTION_PERMANENT,
    )


def test_catalog_falls_back_to_pending_source(monkeypatch):
    """Inactive binding → current pending behavior is preserved."""
    repo = _QRepo(
        sources=[_pink_source(), _mc_source(active=False)],
        instruments=[_q_instrument()],
        bindings=[_binding(active=False)],
    )
    _wire_queries(monkeypatch, repo)
    catalog = mdq.get_catalog()
    inst = catalog["instruments"][0]
    assert inst["source_id"] == "world-bank-pink-sheet"
    assert inst["granularity"] == "month"
    assert inst["data_access_allowed"] is False
    assert inst["selectable_in_ui"] is True


def test_catalog_effective_metalcharts_binding(monkeypatch):
    """Active binding + active displayable source → daily granularity
    and metalcharts source surface for the SAME instrument code."""
    repo = _QRepo(
        sources=[_pink_source(), _mc_source(active=True)],
        instruments=[_q_instrument()],
        bindings=[_binding()],
    )
    _wire_queries(monkeypatch, repo)
    catalog = mdq.get_catalog()
    inst = catalog["instruments"][0]
    assert inst["source_id"] == PROVIDER_METALCHARTS
    assert inst["granularity"] == "day"
    assert set(inst["supported_granularities"]) == {
        "day", "week", "month", "year"
    }
    assert inst["data_access_allowed"] is True
    assert inst["unit_code"] == "usd_per_pound"


def test_observations_read_from_cache_for_ttl_source(monkeypatch):
    cache_row = {
        "observation_id": 1,
        "observation_date": date(2026, 10, 26),
        "native_price": Decimal("6.69"),
        "native_currency": "USD",
        "unit_code": "usd_per_pound",
        "quote_basis": "daily_close",
        "quality_status": "validated",
        "source_id": PROVIDER_METALCHARTS,
        "source_record_key": "metalcharts:HG:2026-10-26",
        "retrieved_at": datetime(2026, 10, 27, tzinfo=timezone.utc),
        "revised_at": None,
    }
    repo = _QRepo(
        sources=[_pink_source(), _mc_source(active=True)],
        instruments=[_q_instrument()],
        bindings=[_binding()],
        cache_rows=[cache_row],
    )
    _wire_queries(monkeypatch, repo)
    out = mdq.list_metal_observations(
        instrument_code="copper",
        date_from_raw="2026-10-01",
        date_to_raw="2026-10-27",
        limit_raw=None,
        cursor_raw=None,
    )
    assert ("cache", {
        "instrument_id": 7,
        "source_id": PROVIDER_METALCHARTS,
        "date_from": date(2026, 10, 1),
        "date_to": date(2026, 10, 27),
        "limit": 100,
        "cursor": None,
    }) in repo.calls
    assert not any(c[0] == "permanent" for c in repo.calls)
    assert out["meta"]["source_ids"] == [PROVIDER_METALCHARTS]
    assert out["items"][0]["price"] == "6.69"
    assert out["items"][0]["unit"] == "usd_per_pound"


def test_observations_pending_source_still_denied(monkeypatch):
    repo = _QRepo(
        sources=[_pink_source(), _mc_source(active=False)],
        instruments=[_q_instrument()],
        bindings=[_binding(active=False)],
    )
    _wire_queries(monkeypatch, repo)
    with pytest.raises(UseNotApprovedError):
        mdq.list_metal_observations(
            instrument_code="copper",
            date_from_raw="2026-10-01",
            date_to_raw="2026-10-27",
            limit_raw=None,
            cursor_raw=None,
        )


def test_params_hash_stable():
    assert params_hash("HG", "2026-10-01", "2026-10-27", "1d") == params_hash(
        "HG", "2026-10-01", "2026-10-27", "1d"
    )
    assert params_hash("HG", "a") != params_hash("HG", "b")
