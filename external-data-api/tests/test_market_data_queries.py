"""Market data read use cases — validation and shaping (PROC-0076)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.application import market_data_queries as mdq
from app.application.contracts import (
    InvalidQueryError,
    StorageUnavailableError,
    UnknownInstrumentError,
    UnknownSeriesError,
    UseNotApprovedError,
)
from app.domain.market_data import (
    MetalInstrument,
    MarketDataSource,
)
from app.infrastructure.config.settings import Settings


class _FakeConnCtx:
    def __enter__(self):
        return object()

    def __exit__(self, *exc):
        return False


def _instrument(**over):
    base = dict(
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
    base.update(over)
    return MetalInstrument(**base)


def _source(**over):
    base = dict(
        source_id="world-bank-pink-sheet",
        provider_id="world-bank-pink-sheet",
        source_kind="file",
        attribution="World Bank — Pink Sheet",
        license_reference="CC BY 4.0",
        license_reviewed_at=date(2026, 10, 26),
        allowed_use_scope="collect;store;derive;internal_display",
        active=True,
    )
    base.update(over)
    return MarketDataSource(**base)


class FakeRepo:
    def __init__(self, **behaviour):
        self.behaviour = behaviour
        self.calls = []

    def list_sources(self):
        return self.behaviour.get(
            "sources",
            [
                _source(),
                _source(
                    source_id="bcb-ptax",
                    provider_id="bcb-ptax",
                    attribution="Banco Central do Brasil — PTAX",
                    license_reference="ODbL-1.0",
                ),
            ],
        )

    def get_source(self, source_id):
        for s in self.list_sources():
            if s.source_id == source_id:
                return s
        return None

    def list_instruments(self):
        return self.behaviour.get("instruments", [_instrument()])

    def get_instrument(self, code):
        for i in self.list_instruments():
            if i.instrument_code == code:
                return i
        return None

    def latest_observation_dates(self):
        return self.behaviour.get("latest", {})

    def list_metal_observations(self, **kw):
        self.calls.append(("list_metal_observations", kw))
        return self.behaviour.get("metal_rows", [])

    def list_fx_observations(self, **kw):
        self.calls.append(("list_fx_observations", kw))
        return self.behaviour.get("fx_rows", [])

    def feed_statuses(self):
        return self.behaviour.get("feeds", [])


@pytest.fixture()
def storage_on(monkeypatch):
    monkeypatch.setattr(
        Settings, "plugins_db_configured", classmethod(lambda cls: True)
    )


@pytest.fixture()
def storage_off(monkeypatch):
    monkeypatch.setattr(
        Settings, "plugins_db_configured", classmethod(lambda cls: False)
    )


def _wire(monkeypatch, repo):
    monkeypatch.setattr(mdq, "get_connection", lambda: _FakeConnCtx())
    monkeypatch.setattr(
        mdq, "MarketDataRepository", lambda conn, schema: repo
    )


def _metal_row(**over):
    base = dict(
        observation_id=1,
        observation_date=date(2026, 9, 1),
        native_price=Decimal("9500.5"),
        native_currency="USD",
        unit_code="metric_ton",
        quote_basis="monthly_average",
        quality_status="validated",
        source_id="world-bank-pink-sheet",
        source_record_key="pink-sheet:2026M09:Copper",
        retrieved_at=datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc),
        revised_at=None,
    )
    base.update(over)
    return base


def _fx_row(**over):
    base = dict(
        fx_id=3,
        pair_code="USD/BRL",
        rate_kind="ptax_closing_sell",
        reference_date=date(2026, 10, 9),
        value=Decimal("5.4321"),
        quality_status="validated",
        source_id="bcb-ptax",
        retrieved_at=datetime(2026, 10, 9, 20, 0, tzinfo=timezone.utc),
        revised_at=None,
    )
    base.update(over)
    return base


# --- storage gate -----------------------------------------------------------


def test_catalog_fails_closed_without_db(storage_off, monkeypatch):
    with pytest.raises(StorageUnavailableError):
        mdq.get_catalog()


def test_observations_fail_closed_without_db(storage_off, monkeypatch):
    with pytest.raises(StorageUnavailableError):
        mdq.list_metal_observations(
            instrument_code="copper",
            date_from_raw="2026-01-01",
            date_to_raw="2026-12-31",
            limit_raw=None,
            cursor_raw=None,
        )


# --- catalog ----------------------------------------------------------------


def test_catalog_lists_instruments_sources_and_fx(
    storage_on, monkeypatch
):
    repo = FakeRepo(latest={"copper": date(2026, 9, 1)})
    _wire(monkeypatch, repo)
    payload = mdq.get_catalog()
    codes = {i["instrument_code"] for i in payload["instruments"]}
    assert "copper" in codes
    assert payload["fx_series"][0]["pair"] == "USD/BRL"
    assert "ptax_closing_sell" in payload["fx_series"][0]["rate_kinds"]
    assert payload["sources"][0]["license_reference"] == "CC BY 4.0"
    assert payload["meta"]["schema_version"] == "v1"


# --- metals observations ----------------------------------------------------


def test_metal_observations_positive(storage_on, monkeypatch):
    repo = FakeRepo(metal_rows=[_metal_row()])
    _wire(monkeypatch, repo)
    payload = mdq.list_metal_observations(
        instrument_code="copper",
        date_from_raw="2026-09-01",
        date_to_raw="2026-09-30",
        limit_raw=None,
        cursor_raw=None,
    )
    item = payload["items"][0]
    assert item["price"] == "9500.5"  # decimal preserved as string
    assert item["currency"] == "USD"
    assert item["quote_basis"] == "monthly_average"
    assert item["source"]["license_reference"] == "CC BY 4.0"
    assert payload["meta"]["data_status"] == "ok"


def test_metal_observations_empty_is_no_data_not_zero(
    storage_on, monkeypatch
):
    _wire(monkeypatch, FakeRepo())
    payload = mdq.list_metal_observations(
        instrument_code="copper",
        date_from_raw="2025-01-01",
        date_to_raw="2025-01-31",
        limit_raw=None,
        cursor_raw=None,
    )
    assert payload["items"] == []
    assert payload["meta"]["data_status"] == "no_data"
    assert "price" not in payload


def test_metal_observations_sibling_instrument(storage_on, monkeypatch):
    repo = FakeRepo(
        instruments=[_instrument(), _instrument(
            instrument_code="aluminum", instrument_id=8,
            metal_code="aluminum", label="Alumínio",
            source_series_key="Aluminum",
        )],
        metal_rows=[_metal_row(observation_id=9)],
    )
    _wire(monkeypatch, repo)
    payload = mdq.list_metal_observations(
        instrument_code="aluminum",
        date_from_raw="2026-09-01",
        date_to_raw="2026-09-30",
        limit_raw=None,
        cursor_raw=None,
    )
    assert payload["items"][0]["instrument_code"] == "aluminum"


def test_unknown_instrument_404(storage_on, monkeypatch):
    _wire(monkeypatch, FakeRepo())
    with pytest.raises(UnknownInstrumentError):
        mdq.list_metal_observations(
            instrument_code="not-a-metal",
            date_from_raw="2026-09-01",
            date_to_raw="2026-09-30",
            limit_raw=None,
            cursor_raw=None,
        )


@pytest.mark.parametrize(
    "date_from,date_to",
    [
        ("bad-date", "2026-09-30"),
        ("2026-09-30", "2026-09-01"),  # inverted
    ],
)
def test_invalid_dates_400(storage_on, monkeypatch, date_from, date_to):
    _wire(monkeypatch, FakeRepo())
    with pytest.raises(InvalidQueryError):
        mdq.list_metal_observations(
            instrument_code="copper",
            date_from_raw=date_from,
            date_to_raw=date_to,
            limit_raw=None,
            cursor_raw=None,
        )


def test_range_cap_400(storage_on, monkeypatch):
    _wire(monkeypatch, FakeRepo())
    with pytest.raises(InvalidQueryError):
        mdq.list_metal_observations(
            instrument_code="copper",
            date_from_raw="2010-01-01",
            date_to_raw="2026-12-31",
            limit_raw=None,
            cursor_raw=None,
        )


def test_bad_cursor_400(storage_on, monkeypatch):
    _wire(monkeypatch, FakeRepo())
    with pytest.raises(InvalidQueryError):
        mdq.list_metal_observations(
            instrument_code="copper",
            date_from_raw="2026-01-01",
            date_to_raw="2026-12-31",
            limit_raw=None,
            cursor_raw="@@@",
        )


def test_limit_bounds(storage_on, monkeypatch):
    _wire(monkeypatch, FakeRepo())
    with pytest.raises(InvalidQueryError):
        mdq.list_metal_observations(
            instrument_code="copper",
            date_from_raw="2026-01-01",
            date_to_raw="2026-12-31",
            limit_raw="999",
            cursor_raw=None,
        )


def test_pagination_emits_cursor(storage_on, monkeypatch):
    rows = [
        _metal_row(observation_id=i, observation_date=date(2026, m, 1))
        for m, i in ((8, 1), (9, 2), (10, 3))
    ]
    repo = FakeRepo(metal_rows=rows + [_metal_row(observation_id=99)])
    _wire(monkeypatch, repo)
    payload = mdq.list_metal_observations(
        instrument_code="copper",
        date_from_raw="2026-01-01",
        date_to_raw="2026-12-31",
        limit_raw="3",
        cursor_raw=None,
    )
    assert len(payload["items"]) == 3
    assert payload["page_info"]["has_more"] is True
    assert payload["page_info"]["next_cursor"]
    # cursor is opaque but decodes back to the last row.
    from app.infrastructure.persistence.market_data_repository import (
        decode_cursor,
    )

    assert decode_cursor(payload["page_info"]["next_cursor"]) == (
        date(2026, 10, 1),
        3,
    )


# --- fx observations --------------------------------------------------------


def test_fx_observations_positive(storage_on, monkeypatch):
    _wire(monkeypatch, FakeRepo(fx_rows=[_fx_row()]))
    payload = mdq.list_fx_observations(
        pair="USD/BRL",
        rate_kind="ptax_closing_sell",
        date_from_raw="2026-10-01",
        date_to_raw="2026-10-31",
        limit_raw=None,
        cursor_raw=None,
    )
    item = payload["items"][0]
    assert item["value"] == "5.4321"
    assert item["rate_kind"] == "ptax_closing_sell"
    assert payload["series"]["unit"] == "BRL per USD"


def test_fx_unknown_pair_404(storage_on, monkeypatch):
    _wire(monkeypatch, FakeRepo())
    with pytest.raises(UnknownSeriesError):
        mdq.list_fx_observations(
            pair="EUR/BRL",
            rate_kind="ptax_closing_sell",
            date_from_raw="2026-10-01",
            date_to_raw="2026-10-31",
            limit_raw=None,
            cursor_raw=None,
        )


def test_fx_unknown_rate_kind_404(storage_on, monkeypatch):
    _wire(monkeypatch, FakeRepo())
    with pytest.raises(UnknownSeriesError):
        mdq.list_fx_observations(
            pair="USD/BRL",
            rate_kind="spot_invented",
            date_from_raw="2026-10-01",
            date_to_raw="2026-10-31",
            limit_raw=None,
            cursor_raw=None,
        )


def test_fx_daily_window_cap(storage_on, monkeypatch):
    _wire(monkeypatch, FakeRepo())
    with pytest.raises(InvalidQueryError):
        mdq.list_fx_observations(
            pair="USD/BRL",
            rate_kind="ptax_closing_sell",
            date_from_raw="2024-01-01",
            date_to_raw="2026-12-31",
            limit_raw=None,
            cursor_raw=None,
        )


# --- ingestion status -------------------------------------------------------


def test_ingestion_status_reports_feeds(storage_on, monkeypatch):
    feeds = [
        dict(
            feed="fx-daily",
            last_run_started_at=datetime(2026, 10, 26, 9, 0, tzinfo=timezone.utc),
            last_run_finished_at=datetime(2026, 10, 26, 9, 1, tzinfo=timezone.utc),
            last_outcome="success",
            last_error_code=None,
            last_successful_at=datetime(2026, 10, 26, 9, 1, tzinfo=timezone.utc),
            latest_observation_date=date(2026, 10, 24),
            observation_count=400,
        )
    ]
    repo = FakeRepo(feeds=feeds, sources=[_source()])
    _wire(monkeypatch, repo)
    payload = mdq.get_ingestion_status()
    assert payload["feeds"][0]["feed"] == "fx-daily"
    assert payload["feeds"][0]["latest_observation_date"] == "2026-10-24"


# --- use-rights quarantine (R1.2) -------------------------------------------

LME_PENDING_SCOPE = (
    "collect;store;derive;internal_display_pending_lme_review;"
    "no_redistribution_pending_lme_review"
)


def _pending_repo(**kw):
    return FakeRepo(
        sources=[_source(allowed_use_scope=LME_PENDING_SCOPE)], **kw
    )


def test_pending_display_scope_blocks_metal_observations(
    storage_on, monkeypatch
):
    """AC-R1.2-06/07/08: LME-pending scope denies the read before a
    single row is fetched — no prices ever leave the producer."""
    repo = _pending_repo(metal_rows=[_metal_row()])
    _wire(monkeypatch, repo)
    with pytest.raises(UseNotApprovedError) as exc:
        mdq.list_metal_observations(
            instrument_code="copper",
            date_from_raw="2026-09-01",
            date_to_raw="2026-09-30",
            limit_raw=None,
            cursor_raw=None,
        )
    assert exc.value.code == "EXTERNAL_DATA_USE_NOT_APPROVED"
    assert repo.calls == []  # zero observation queries executed


def test_pending_display_scope_blocks_fx_observations(
    storage_on, monkeypatch
):
    bcb_pending = _source(
        source_id="bcb-ptax",
        allowed_use_scope="collect;store;internal_display_pending_review",
    )
    repo = FakeRepo(sources=[bcb_pending], fx_rows=[_fx_row()])
    _wire(monkeypatch, repo)
    with pytest.raises(UseNotApprovedError):
        mdq.list_fx_observations(
            pair="USD/BRL",
            rate_kind="ptax_closing_sell",
            date_from_raw="2026-10-01",
            date_to_raw="2026-10-31",
            limit_raw=None,
            cursor_raw=None,
        )
    assert repo.calls == []


def test_catalog_flags_unavailable_instrument_without_prices(
    storage_on, monkeypatch
):
    """AC-R1.2-08/12: the catalog still lists the instrument with its
    provenance, but marks display_allowed=False — availability is a
    contract field, never leaked prices."""
    repo = _pending_repo(latest={"copper": date(2026, 9, 1)})
    _wire(monkeypatch, repo)
    payload = mdq.get_catalog()
    copper = next(
        i for i in payload["instruments"] if i["instrument_code"] == "copper"
    )
    assert copper["display_allowed"] is False
    assert "price" not in copper and "value" not in copper
    fx = payload["fx_series"][0]
    assert fx["display_allowed"] is False  # same source? no — bcb absent
    sources = {s["source_id"]: s for s in payload["sources"]}
    assert sources["world-bank-pink-sheet"]["allowed_use_scope"] == (
        LME_PENDING_SCOPE
    )


def test_ingestion_status_exposes_allowed_use_scope(storage_on, monkeypatch):
    feeds = [
        dict(
            feed="metals-monthly",
            last_run_started_at=None,
            last_run_finished_at=None,
            last_outcome=None,
            last_error_code=None,
            last_successful_at=None,
            latest_observation_date=None,
            observation_count=0,
        )
    ]
    repo = FakeRepo(feeds=feeds, sources=[_source()])
    _wire(monkeypatch, repo)
    payload = mdq.get_ingestion_status()
    assert payload["feeds"][0]["source_allowed_use_scope"] == (
        "collect;store;derive;internal_display"
    )
